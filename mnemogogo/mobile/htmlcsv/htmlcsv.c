/*
 * Copyright (c) 2009 Timothy Bourke
 * All rights reserved.
 *
 * This program is free software; you can redistribute it and/or modify it
 * under the terms of the "BSD License" which is distributed with the
 * software in the file ../LICENSE.
 *
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the BSD
 * License for more details.
 */
/*
 * Certain routines Copyright (c) Peter Bienstman <Peter.Bienstman@UGent.be>
 */

#include "htmlcsv.h"

#include <ctype.h>
#include <time.h>
#include <string.h>
#include <assert.h>

#define PATH_SEP '/'

#define LEN_STAT_LINE 63
#define NUM_STATS 12
// NB: these specifiers must match the stat datatypes
#define STATLINE_FORMAT "%1hhx,%04hx,%04hx,%04hx,%04hx,%04hx,%04hx,%08x,%08x,%1hhx,%04hx,%04hx\n"

#define STAT_FORMAT "gr=%1d e=%2.03f r=%4d l=%4d ds=%6d"
char statstring[] = "gr=0 e=00.000 r=0000 l=0000 ds=00000";

#define LEN_HTMLFILENAME 10
char htmlfilenamestr[LEN_HTMLFILENAME];

const char *errorstrs[] = {
    "file not found",
    "could not allocate memory",
    "corrupt database",
    "error writing to database",
};

#define MAX_LINE 100
char line[MAX_LINE];

int initial_interval[] = {0, 0, 1, 3, 4, 5};

// stats
typedef unsigned char grade_t; 
typedef unsigned short stat_t;
typedef unsigned char cat_t;
typedef unsigned char bool_t;

#define NO_INVERSE 0xffff

typedef struct cardstats {
    grade_t grade;
    stat_t easiness;
    stat_t acq_reps;
    stat_t ret_reps;
    stat_t lapses;
    stat_t acq_reps_since_lapse;
    stat_t ret_reps_since_lapse;
    time_t last_rep;
    time_t next_rep;
    bool_t unseen;
    card_t inverse;
    cat_t category;
    bool_t skip;
} cardstats_t;

int nstats = 0;
cardstats_t *stats = NULL;

// options
stat_t grade_0_items_at_once = 10;
bool_t sorting = 1;
bool_t logging = 1;
stat_t day_starts_at = 3;

// revision queue

typedef struct {
    card_t *q;

    int num_scheduled;
    int idx_new;
    int limit_new;

    int size;
    int curr;

    int first;
}  revqueue_t;

revqueue_t revqueue;

time_t days_since_start = 0;

FILE* logfile = NULL;
float thinking_time = 0.0;

// functions

int getdecimal(FILE* f)
{
    int c;
    int n = 0;

    while (isdigit(c = fgetc(f))) {
	n = n * 10 + (c - '0');
    }

    return n;
}

char* splitconfigline(char* line)
{
    char* value = NULL;

    while (*line && *line != '=')
	++line;

    if (*line != '=')
	return NULL;

    *line++ = '\0';
    value = line;

    while (*line && *line != '\n')
	++line;

    *line = '\0';

    return value;
}

void write_config(FILE *f)
{
    fprintf(f, "grade_0_items_at_once=%hd\n", grade_0_items_at_once);
    fprintf(f, "sorting=%hhd\n", sorting);
    fprintf(f, "logging=%hhd\n", logging);
    fprintf(f, "day_starts_at=%hd\n", day_starts_at);
}

void read_config(char* fpath)
{
    FILE *fin;
    char *value;

    if (!(fin = fopen(fpath, "r")))
	return;

    while (fgets(line, MAX_LINE, fin)) {
	value = splitconfigline(line);
	if (strcmp(line, "grade_0_items_at_once") == 0) {
	    sscanf(value, "%hd", &grade_0_items_at_once);
	} else if (strcmp(line, "sorting") == 0) {
	    sscanf(value, "%hhd", &sorting);
	} else if (strcmp(line, "logging") == 0) {
	    sscanf(value, "%hhd", &logging);
	} else if (strcmp(line, "day_starts_at") == 0) {
	    sscanf(value, "%hd", &day_starts_at);
	}
    }

    fclose(fin);
}

void initrevqueue(void)
{
    revqueue.num_scheduled = 0;
    revqueue.idx_new = nstats - 1;
    revqueue.limit_new = nstats;
    revqueue.curr = 0;
    revqueue.first = 1;
}

void freecarddb(void)
{
    free(stats);
    free(revqueue.q);
    stats = NULL;
    revqueue.q = NULL;
    initrevqueue();
    nstats = 0;
    if (logfile != NULL) {
	fclose(logfile);
	logfile = NULL;
    }
}

char* join(char *dst, char* path, char* file)
{
    if (dst == NULL) {
	return file;
    } else {
	sprintf(dst, "%s%c%s", path, PATH_SEP, file);
	return dst;
    }
}

int loadcarddb(char* path)
{
    FILE* fin;
    int r, i = 0;
    char* fpath = NULL;
    int start_time;
    time_t adjusted_now;
    int err;

    srand(time(NULL));

    if (path != NULL)
	fpath = malloc(strlen(path) + 12);
    if (fpath == NULL)
	return ERROR_MALLOC;

    // calculate days_since_start
    if (!(fin = fopen(join(fpath, path, "start_time"), "r"))) {
	err = ERROR_FILE_NOT_FOUND;
	goto error;
    }
    start_time = getdecimal(fin);
    fclose(fin);
    adjusted_now = (time_t)time(NULL) - (day_starts_at * 3600);
    days_since_start = (adjusted_now - start_time) / 86400;

    // read configuration 
    read_config(join(fpath, path, "config"));

    // read card stats
    if (!(fin = fopen(join(fpath, path, "stats.csv"), "r"))) {
	err = ERROR_FILE_NOT_FOUND;
	goto error;
    }

    nstats = getdecimal(fin);
    stats = calloc(nstats, sizeof(cardstats_t));

    initrevqueue();
    revqueue.size = nstats;
    revqueue.q = calloc(revqueue.size, sizeof(card_t));

    if (stats == NULL || revqueue.q == NULL) {
	err = ERROR_MALLOC;
	goto error;
    }

    while ((i < nstats) && fgets(line, LEN_STAT_LINE, fin)) {
	r = sscanf(line, STATLINE_FORMAT, &stats[i].grade,
					  &stats[i].easiness,
					  &stats[i].acq_reps,
					  &stats[i].ret_reps,
					  &stats[i].lapses,
					  &stats[i].acq_reps_since_lapse,
					  &stats[i].ret_reps_since_lapse,
					  &stats[i].last_rep,
					  &stats[i].next_rep,
					  &stats[i].unseen,
					  &stats[i].category,
					  &stats[i].inverse);
	stats[i].skip = 0;
	++i;

	if (r != NUM_STATS) {
	    err = ERROR_CORRUPT_DB;
	    goto error;
	}
    }

    fclose(fin);
    fin = NULL;

    if (i < nstats) {
	err = ERROR_CORRUPT_DB;
	goto error;
    }

    if (logging) {
	logfile = fopen(join(fpath, path, "prelog"), "a");
    } else {
	logfile = NULL;
    }

    return i;

error:
    if (fpath != NULL)
	free(fpath);
    if (fin != NULL)
	fclose(fin);
    return err;
}

int writecard(FILE* f, card_t i)
{
	return (fprintf(f, STATLINE_FORMAT, stats[i].grade,
					    stats[i].easiness,
					    stats[i].acq_reps,
					    stats[i].ret_reps,
					    stats[i].lapses,
					    stats[i].acq_reps_since_lapse,
					    stats[i].ret_reps_since_lapse,
					    stats[i].last_rep,
					    stats[i].next_rep,
					    stats[i].unseen,
					    stats[i].category,
					    stats[i].inverse));
}
    
int writecarddb(FILE* f)
{
    card_t i, r;

    for (i=0; i < nstats; ++i) {
	r = writecard(f, i);
	if (r != LEN_STAT_LINE - 1)
	    return ERROR_WRITING_DB;
    }

    return r;
}

int savecarddb(char* path)
{
    FILE* fout;
    int r;
    char* fpath = NULL;

    if (path != NULL)
	fpath = malloc(strlen(path) + 12);

    if (!(fout = fopen(join(fpath, path, "stats.csv"), "w"))) {
	if (fpath != NULL)
	    free(fpath);
	return ERROR_WRITING_DB;
    }

    fprintf(fout, "%d\n", nstats);
    r = writecarddb(fout);
    fclose(fout);

    if (fpath != NULL)
	free(fpath);
    return r;
}

char* printstats(card_t i)
{
    sprintf(statstring, STAT_FORMAT,
		(int)stats[i].grade,
		(float)stats[i].easiness / 1000.0,
		(int)stats[i].acq_reps + stats[i].ret_reps,
		(int)stats[i].lapses,
		days_since_start - stats[i].last_rep);

    return statstring;
}

const char* errorstr(int err)
{
    return errorstrs[abs(err) - 1];
}

// Adapted directly from Peter Bienstman's Mnemosyne 1.x
int is_due_for_retention_rep(card_t i, int days)
{
    return ((stats[i].grade >= 2)
		&& (days_since_start >= stats[i].next_rep - days));
}

// Adapted directly from Peter Bienstman's Mnemosyne 1.x
int is_due_for_acquisition_rep(card_t i, int days)
{
    return (stats[i].grade < 2);
}

int sort_key_interval(card_t i)
{
    return (stats[i].next_rep - stats[i].last_rep);
}

int swap_revqueue(int i, int j)
{
    card_t tmp = revqueue.q[i];
    revqueue.q[i] = revqueue.q[j];
    revqueue.q[j] = tmp;
}

// insertion sort: linear when already ordered, won't blow the stack
// if too slow: implement shell sort
void sort_scheduled()
{
    int i, j;
    card_t c;
    int key;

    for (i=1; i < revqueue.num_scheduled; ++i) {
	c = revqueue.q[i];
	key = sort_key_interval(c);

	for (j=i-1; j >= 0 && sort_key_interval(revqueue.q[j]) > key; --j)
	    revqueue.q[j + 1] = revqueue.q[j];
	revqueue.q[j + 1] = c;
    }
}

int randint(int lower, int upper)
{
    return (lower + rand() % (upper - lower + 1));
}

void shuffle_revqueue(int first, int max)
{
    int i;

    for (i=first; i < max; ++i)
	swap_revqueue(i, randint(first, max - 1));
}

int p_rememorise0(int ri)
{
    int i = revqueue.q[ri];
    return (stats[i].lapses > 0 && stats[i].grade == 0);
}

int p_rememorise1(int ri)
{
    int i = revqueue.q[ri];
    return (stats[i].lapses > 0 && stats[i].grade == 1);
}

int p_seenbutnotmemorised0(int ri)
{
    int i = revqueue.q[ri];
    return (stats[i].lapses == 0
	    && stats[i].unseen == 0
	    && stats[i].grade == 0);
}

int p_seenbutnotmemorised1(int ri)
{
    int i = revqueue.q[ri];
    return (stats[i].lapses == 0
	    && stats[i].unseen == 0
	    && stats[i].grade == 1);
}

int cluster_revqueue(int first, int max, int (*p)(int))
{
    int i;
    int hd = first;

    for (i=first; i < max; ++i) {
	if (p(revqueue.q[i]))
	    swap_revqueue(i, hd++);
    }

    return hd;
}

// Adapted directly from Peter Bienstman's Mnemosyne 1.x
void buildrevisionqueue(void)
{
    int i;

    initrevqueue();

    // form two queues:
    //	    cards scheduled for today upward from 0
    //	    wrong and unmemorised cards downward from revqueue.size
    
    for (i=0; i < nstats; ++i) {
	if (is_due_for_retention_rep(i, 0)) {
	    revqueue.q[revqueue.num_scheduled++] = i;

	} else if (is_due_for_acquisition_rep(i, 0)) {
	    revqueue.q[revqueue.idx_new--] = i;
	}
    }

    if (sorting) {
	sort_scheduled();
    } else {
	shuffle_revqueue(0, revqueue.num_scheduled);
    }
    shuffle_revqueue(revqueue.idx_new + 1, nstats);

    i = cluster_revqueue(revqueue.idx_new + 1, nstats, p_rememorise0);
    i = cluster_revqueue(i, nstats, p_rememorise1);
    i = cluster_revqueue(i, nstats, p_seenbutnotmemorised0);
    i = cluster_revqueue(i, nstats, p_seenbutnotmemorised1);

    revqueue.limit_new = revqueue.idx_new + 1 + grade_0_items_at_once;
    if (revqueue.limit_new > nstats)
	revqueue.limit_new = nstats;
}

void shiftforgottentonew(void)
{
    int i;

    for (i=revqueue.num_scheduled - 1; i >= 0; --i) {
	if (stats[revqueue.q[i]].grade < 2) {
	    swap_revqueue(i, revqueue.idx_new--);
	}
    }
}

int numscheduled(void)
{
    int n = revqueue.num_scheduled - revqueue.curr;

    if (n < 0)
	return 0;

    return n;
}

int getfirstcard(card_t* next)
{
    revqueue.first = 0;

    if (revqueue.num_scheduled > 0) {
	revqueue.curr = 0;
	*next = revqueue.curr;
	return 1;
    }

    if (revqueue.idx_new + 1 < revqueue.limit_new) {
	revqueue.curr = revqueue.idx_new + 1;
	*next = revqueue.curr;
	return 1;
    }

    return 0;
}

int getcard(card_t* next)
{
    if (revqueue.first)
	return getfirstcard(next);

    if (revqueue.curr >= revqueue.limit_new)
	return 0;

    if (revqueue.curr + 1 < revqueue.num_scheduled) {
	*next = ++revqueue.curr;
	return 1;
    }

    if (revqueue.curr + 1 == revqueue.num_scheduled) {
	shiftforgottentonew();
	revqueue.curr = revqueue.idx_new + 1;

    } else if (stats[revqueue.curr].grade < 2) {
	// shuffle grade 0 cards back into set
	swap_revqueue(revqueue.curr, randint(revqueue.curr,
					     revqueue.limit_new - 1));

    } else if (stats[revqueue.curr].unseen == 1) {
	// shift the limit forward
	++revqueue.limit_new;
	++revqueue.curr;

    } else {
	++revqueue.curr;
    }

    while (revqueue.curr < revqueue.size
	   && stats[revqueue.curr].skip && stats[revqueue.curr].unseen) {
	++revqueue.curr;
	++revqueue.limit_new;
    }

    if (revqueue.limit_new > nstats)
	revqueue.limit_new = nstats;

    if (revqueue.curr >= revqueue.limit_new)
	return 0;
    
    *next = revqueue.curr;
    return 1;
}

float easiness(stat_t val, stat_t easiness)
{
    return val * ((float)easiness / 1000.0);
}

// Adapted directly from Peter Bienstman's Mnemosyne 1.x
int calculate_interval_noise(int interval)
{
    int a;

    if (interval == 0) {
        return 0;

    } else if (interval == 1) {
        return randint(0, 1);

    } else if (interval <= 10) {
        return randint(-1, 1);

    } else if (interval <= 60) {
        return randint(-3, 3);

    } else {
        a = interval / 20;
        return randint(-a, a);
    }
}

// Adapted directly from Peter Bienstman's Mnemosyne 1.x
void processanswer(card_t i, int new_grade)
{
    stat_t scheduled_interval;
    stat_t actual_interval;
    float new_interval;
    cardstats_t* item = &stats[i];
    int noise;

    // Don't schedule inverse or identical questions on the same day.
    if (item->inverse != NO_INVERSE)
	stats[item->inverse].skip = 1;

    // Calculate scheduled and actual interval, taking care of corner
    // case when learning ahead on the same day.
    
    scheduled_interval = item->next_rep   - item->last_rep;
    actual_interval    = days_since_start - item->last_rep;

    if (actual_interval == 0)
        actual_interval = 1; // Otherwise new interval can become zero.

    if (item->acq_reps == 0 && item->ret_reps == 0) { // item->is_new()

        // The item is not graded yet, e.g. because it is imported.

        item->acq_reps = 1;
        item->acq_reps_since_lapse = 1;

        new_interval = initial_interval[new_grade];

    } else if (item->grade < 2 && new_grade < 2) {
        // In the acquisition phase and staying there.
        item->acq_reps += 1;
        item->acq_reps_since_lapse += 1;
        new_interval = 0.0;

    } else if (item->grade < 2 && new_grade >= 2 && new_grade <= 5) {
         // In the acquisition phase and moving to the retention phase.
         item->acq_reps += 1;
         item->acq_reps_since_lapse += 1;
         new_interval = 1.0;

    } else if ((item->grade >= 2 && item->grade <= 5) && new_grade < 2) {
         // In the retention phase and dropping back to the acquisition phase.
         item->ret_reps += 1;
         item->lapses += 1;
         item->acq_reps_since_lapse = 0;
         item->ret_reps_since_lapse = 0;

         new_interval = 0.0;

         // Move this item to the front of the list, to have precedence over
         // items which are still being learned for the first time.
	 // THIS IS NOW DONE IN shiftforgottentonew()

    } else if ((item->grade >= 2 && item->grade <= 5)
		&& (new_grade >= 2 && new_grade <= 5)) {
        // In the retention phase and staying there.
        item->ret_reps += 1;
        item->ret_reps_since_lapse += 1;

        if (actual_interval >= scheduled_interval) {
            if (new_grade == 2) {
                item->easiness -= 160;
	    } else if (new_grade == 3) {
                item->easiness -= 140;
	    } else if (new_grade == 5) {
                item->easiness += 100;
	    } else if (item->easiness < 1.3) {
                item->easiness = 1300;
	    }
	}
            
        new_interval = 0.0;
        
        if (item->ret_reps_since_lapse == 1) {
            new_interval = 6.0;

	} else {
            if (new_grade == 2 || new_grade == 3) {
                if (actual_interval <= scheduled_interval) {
                    new_interval = easiness(actual_interval, item->easiness);
		} else {
                    new_interval = scheduled_interval;
		}

	    } else if (new_grade == 4) {
                new_interval = easiness(actual_interval, item->easiness);

	    } else if (new_grade == 5) {
                if (actual_interval < scheduled_interval) {
                    new_interval = scheduled_interval; // Avoid spacing.
		} else {
                    new_interval = easiness(actual_interval, item->easiness);
		}
	    }
	}

        // Shouldn't happen, but build in a safeguard.
        if (new_interval == 0)
            new_interval = scheduled_interval;
    }

    // Add some randomness to interval.
    noise = calculate_interval_noise((int)new_interval);

    // Update grade and interval.
    item->grade    = new_grade;
    item->last_rep = days_since_start;
    item->next_rep = days_since_start + (time_t)new_interval + noise;
    item->unseen   = 0;
    
    if (logfile != NULL) {
	// NOTE: the <%d> must be replaced with the id.
	fprintf(logfile, "R <%hd> %d %1.2f | %d %d %d %d %d | %d %d | %d %d | %1.1f\n",
		i,
		item->grade,
		((float)item->easiness) / 1000.0,
		item->acq_reps,
		item->ret_reps,
		item->lapses,
		item->acq_reps_since_lapse,
		item->ret_reps_since_lapse,
		scheduled_interval,
		actual_interval,
		new_interval,
		noise,
		thinking_time);
    }
}

char* htmlfilename(card_t i, int answer)
{
    if (answer == 1) {
	sprintf(htmlfilenamestr, "A%04hx.htm", i);
    } else {
	sprintf(htmlfilenamestr, "Q%04hx.htm", i);
    }
    return htmlfilenamestr;
}

void assertinvariants(void)
{
    assert(sizeof(card_t) >= 2);    // bytes
    assert(sizeof(grade_t) >= 1);   // byte
    assert(sizeof(cat_t) >= 1);	    // byte
    assert(sizeof(bool_t) >= 1);    // byte
    assert(sizeof(stat_t) >= 2);    // bytes
    assert(sizeof(time_t) >= 4);    // bytes

    assert(revqueue.num_scheduled <= (revqueue.idx_new + 1));
    assert(revqueue.idx_new <= revqueue.limit_new);
    assert(revqueue.limit_new <= revqueue.size);
    assert((revqueue.curr <= revqueue.num_scheduled)
	   || ((revqueue.curr > revqueue.idx_new)
	       && (revqueue.curr <= revqueue.limit_new)));
}

void debughtmlcsv(FILE *f, int showqueue)
{
    int i;

    if (showqueue) {
	fprintf(f, "scheduled----------------------\n");
	for (i = 0; i < revqueue.num_scheduled; ++i) {
	    fprintf(f,"%3d serial=%3d key=%d\n", i, revqueue.q[i], 
			sort_key_interval(revqueue.q[i]));
	}
	fprintf(f, "new----------------------------\n");
	for (i = revqueue.idx_new + 1; i < revqueue.size; ++i) {
	    if (i == revqueue.limit_new)
		fprintf(f, "--new limit--\n");
	    fprintf(f, "%3d serial=%3d re0=%d re1=%d sn0=%d sn1=%d\n",
		    i, revqueue.q[i], 
		    p_rememorise0(revqueue.q[i]),
		    p_rememorise1(revqueue.q[i]),
		    p_seenbutnotmemorised0(revqueue.q[i]),
		    p_seenbutnotmemorised1(revqueue.q[i]));
	}
    }
    fprintf(f, "-------------------------------\n");
    fprintf(f, "nstats=%hd\n", nstats);
    fprintf(f, "days_since_start=%hd\n", days_since_start);
    fprintf(f, "revqueue.num_scheduled=%d\n", revqueue.num_scheduled);
    fprintf(f, "revqueue.idx_new=%d\n", revqueue.idx_new);
    fprintf(f, "revqueue.limit_new=%d\n", revqueue.limit_new);
    fprintf(f, "revqueue.size=%d\n", revqueue.size);
    fprintf(f, "revqueue.curr=%d\n", revqueue.curr);
    fprintf(f, "revqueue.first=%d\n", revqueue.first);
}

