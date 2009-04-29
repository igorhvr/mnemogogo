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
#include <string.h>
#include <assert.h>

#define LEN_STAT_LINE 63
#define NUM_STATS 12
// NB: these specifiers must match the stat datatypes
#define STATLINE_FORMAT "%1hhx,%04hx,%04hx,%04hx,%04hx,%04hx,%04hx,%08x,%08x,%1hhx,%04hx,%04hx\n"

#define MAX_LINE 100

const char *errorstrs[] = {
    "file not found",
    "could not allocate memory",
    "corrupt database",
    "error writing to database",
};

const int initial_interval[] = {0, 0, 1, 3, 4, 5};

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

struct _carddb_t {
    int nstats;
    cardstats_t *stats;
    time_t days_since_start;
    FILE* logfile;

    revqueue_t revqueue;

    // options
    stat_t grade_0_items_at_once;
    bool_t sorting;
    bool_t logging;
    stat_t day_starts_at;
};

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

void write_config(carddb_t db, FILE *f)
{
    fprintf(f, "grade_0_items_at_once=%hd\n", db->grade_0_items_at_once);
    fprintf(f, "sorting=%hhd\n", db->sorting);
    fprintf(f, "logging=%hhd\n", db->logging);
    fprintf(f, "day_starts_at=%hd\n", db->day_starts_at);
}

void read_config(carddb_t db, char* fpath)
{
    FILE *fin;
    char *value;
    char line[MAX_LINE];

    if (!(fin = fopen(fpath, "r")))
	return;

    while (fgets(line, MAX_LINE, fin)) {
	value = splitconfigline(line);
	if (strcmp(line, "grade_0_items_at_once") == 0) {
	    sscanf(value, "%hd", &db->grade_0_items_at_once);
	} else if (strcmp(line, "sorting") == 0) {
	    sscanf(value, "%hhd", &db->sorting);
	} else if (strcmp(line, "logging") == 0) {
	    sscanf(value, "%hhd", &db->logging);
	} else if (strcmp(line, "day_starts_at") == 0) {
	    sscanf(value, "%hd", &db->day_starts_at);
	}
    }

    fclose(fin);
}

void initrevqueue(carddb_t db)
{
    db->revqueue.num_scheduled = 0;
    db->revqueue.idx_new = db->nstats - 1;
    db->revqueue.limit_new = db->nstats;
    db->revqueue.curr = 0;
    db->revqueue.first = 1;
}

void freecarddb(carddb_t db)
{
    if (db->stats)
	free(db->stats);
    if (db->revqueue.q)
	free(db->revqueue.q);

    db->stats = NULL;
    db->revqueue.q = NULL;
    initrevqueue(db);
    db->nstats = 0;
    if (db->logfile != NULL) {
	fclose(db->logfile);
	db->logfile = NULL;
    }

    free(db);
}

char* join(char *dst, char* path, char* file)
{
    if (dst == NULL) {
	return file;
    } else {
	sprintf(dst, "%s%s", path, file);
	return dst;
    }
}

carddb_t loadcarddb(char* path, int* err)
{
    FILE* fin;
    int r, i = 0;
    char* fpath = NULL;
    int start_time;
    time_t adjusted_now;
    char line[MAX_LINE];
    carddb_t db;

    db->stats = NULL;
    db->revqueue.q = NULL;
    db->logfile = NULL;
    db->grade_0_items_at_once = 10;
    db->sorting = 1;
    db->logging = 1;
    db->day_starts_at = 3;

    srand(time(NULL));

    db = malloc(sizeof(struct _carddb_t));
    if (db == NULL) {
	*err = ERROR_MALLOC;
	goto error;
    }

    if (path != NULL) {
	fpath = malloc(strlen(path) + 12);
	if (fpath == NULL) {
	    *err = ERROR_MALLOC;
	    goto error;
	}
    }

    // read configuration 
    read_config(db, join(fpath, path, "config"));

    // calculate days_since_start
    if (!(fin = fopen(join(fpath, path, "start_time"), "r"))) {
	*err = ERROR_FILE_NOT_FOUND;
	goto error;
    }
    start_time = getdecimal(fin);
    fclose(fin);
    adjusted_now = (time_t)time(NULL) - (db->day_starts_at * 3600);
    db->days_since_start = (adjusted_now - start_time) / 86400;

    // read card stats
    if (!(fin = fopen(join(fpath, path, "stats.csv"), "r"))) {
	*err = ERROR_FILE_NOT_FOUND;
	goto error;
    }

    db->nstats = getdecimal(fin);
    db->stats = calloc(db->nstats, sizeof(cardstats_t));

    initrevqueue(db);
    db->revqueue.size = db->nstats;
    db->revqueue.q = calloc(db->revqueue.size, sizeof(card_t));

    if (db->stats == NULL || db->revqueue.q == NULL) {
	*err = ERROR_MALLOC;
	goto error;
    }

    while ((i < db->nstats) && fgets(line, LEN_STAT_LINE, fin)) {
	r = sscanf(line, STATLINE_FORMAT, &db->stats[i].grade,
					  &db->stats[i].easiness,
					  &db->stats[i].acq_reps,
					  &db->stats[i].ret_reps,
					  &db->stats[i].lapses,
					  &db->stats[i].acq_reps_since_lapse,
					  &db->stats[i].ret_reps_since_lapse,
					  &db->stats[i].last_rep,
					  &db->stats[i].next_rep,
					  &db->stats[i].unseen,
					  &db->stats[i].category,
					  &db->stats[i].inverse);
	db->stats[i].skip = 0;
	++i;

	if (r != NUM_STATS) {
	    *err = ERROR_CORRUPT_DB;
	    goto error;
	}
    }

    fclose(fin);
    fin = NULL;

    if (i < db->nstats) {
	*err = ERROR_CORRUPT_DB;
	goto error;
    }

    if (db->logging) {
	db->logfile = fopen(join(fpath, path, "prelog"), "a");
    } else {
	db->logfile = NULL;
    }

    *err = i;
    return db;

error:
    if (db != NULL)
	freecarddb(db);
    if (fpath != NULL)
	free(fpath);
    if (fin != NULL)
	fclose(fin);
    return NULL;
}

int writecard(carddb_t db, FILE* f, card_t i)
{
	return (fprintf(f, STATLINE_FORMAT, db->stats[i].grade,
					    db->stats[i].easiness,
					    db->stats[i].acq_reps,
					    db->stats[i].ret_reps,
					    db->stats[i].lapses,
					    db->stats[i].acq_reps_since_lapse,
					    db->stats[i].ret_reps_since_lapse,
					    db->stats[i].last_rep,
					    db->stats[i].next_rep,
					    db->stats[i].unseen,
					    db->stats[i].category,
					    db->stats[i].inverse));
}
    
int writecarddb(carddb_t db, FILE* f)
{
    card_t i, r;

    for (i=0; i < db->nstats; ++i) {
	r = writecard(db, f, i);
	if (r != LEN_STAT_LINE - 1)
	    return ERROR_WRITING_DB;
    }

    return r;
}

int savecarddb(carddb_t db, char* path)
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

    fprintf(fout, "%d\n", db->nstats);
    r = writecarddb(db, fout);
    fclose(fout);

    if (fpath != NULL)
	free(fpath);
    return r;
}

char* printstats(carddb_t db, card_t i, char *statstring)
{
    sprintf(statstring, STAT_FORMAT,
		(int)db->stats[i].grade,
		(float)db->stats[i].easiness / 1000.0,
		(int)db->stats[i].acq_reps + db->stats[i].ret_reps,
		(int)db->stats[i].lapses,
		db->days_since_start - db->stats[i].last_rep);

    return statstring;
}

const char* errorstr(int err)
{
    return errorstrs[abs(err) - 1];
}

// Adapted directly from Peter Bienstman's Mnemosyne 1.x
int is_due_for_retention_rep(carddb_t db, card_t i, int days)
{
    return ((db->stats[i].grade >= 2)
		&& (db->days_since_start >= db->stats[i].next_rep - days));
}

// Adapted directly from Peter Bienstman's Mnemosyne 1.x
int is_due_for_acquisition_rep(carddb_t db, card_t i, int days)
{
    return (db->stats[i].grade < 2);
}

int sort_key_interval(carddb_t db, card_t i)
{
    return (db->stats[i].next_rep - db->stats[i].last_rep);
}

int swap_revqueue(carddb_t db, int i, int j)
{
    card_t tmp = db->revqueue.q[i];
    db->revqueue.q[i] = db->revqueue.q[j];
    db->revqueue.q[j] = tmp;
}

// insertion sort: linear when already ordered, won't blow the stack
// if too slow: implement shell sort
void sort_scheduled(carddb_t db)
{
    int i, j;
    card_t c;
    int key;

    for (i=1; i < db->revqueue.num_scheduled; ++i) {
	c = db->revqueue.q[i];
	key = sort_key_interval(db, c);

	for (j=i-1;
	     j >= 0 && sort_key_interval(db, db->revqueue.q[j]) > key;
	     --j)
	    db->revqueue.q[j + 1] = db->revqueue.q[j];
	db->revqueue.q[j + 1] = c;
    }
}

int randint(int lower, int upper)
{
    return (lower + rand() % (upper - lower + 1));
}

void shuffle_revqueue(carddb_t db, int first, int max)
{
    int i;

    for (i=first; i < max; ++i)
	swap_revqueue(db, i, randint(first, max - 1));
}

int p_rememorise0(carddb_t db, int i)
{
    return (db->stats[i].lapses > 0 && db->stats[i].grade == 0);
}

int p_rememorise1(carddb_t db, int i)
{
    return (db->stats[i].lapses > 0 && db->stats[i].grade == 1);
}

int p_seenbutnotmemorised0(carddb_t db, int i)
{
    return (db->stats[i].lapses == 0
	    && db->stats[i].unseen == 0
	    && db->stats[i].grade == 0);
}

int p_seenbutnotmemorised1(carddb_t db, int i)
{
    return (db->stats[i].lapses == 0
	    && db->stats[i].unseen == 0
	    && db->stats[i].grade == 1);
}

int cluster_revqueue(carddb_t db, int hd, int max, int (*p)(carddb_t, int))
{
    int i;

    for (i=hd; i < max; ++i) {
	if (p(db, db->revqueue.q[i]))
	    swap_revqueue(db, i, hd++);
    }

    return hd;
}

// Adapted directly from Peter Bienstman's Mnemosyne 1.x
void buildrevisionqueue(carddb_t db)
{
    int i;

    initrevqueue(db);

    // form two queues:
    //	    cards scheduled for today upward from 0
    //	    wrong and unmemorised cards downward from revqueue.size
    
    for (i=0; i < db->nstats; ++i) {
	if (is_due_for_retention_rep(db, i, 0)) {
	    db->revqueue.q[db->revqueue.num_scheduled++] = i;

	} else if (is_due_for_acquisition_rep(db, i, 0)) {
	    db->revqueue.q[db->revqueue.idx_new--] = i;
	}
    }

    if (db->sorting) {
	sort_scheduled(db);
    } else {
	shuffle_revqueue(db, 0, db->revqueue.num_scheduled);
    }
    shuffle_revqueue(db, db->revqueue.idx_new + 1, db->nstats);

    i = cluster_revqueue(db, db->revqueue.idx_new + 1,
			 db->nstats, p_rememorise0);
    i = cluster_revqueue(db, i, db->nstats, p_rememorise1);
    i = cluster_revqueue(db, i, db->nstats, p_seenbutnotmemorised0);
    i = cluster_revqueue(db, i, db->nstats, p_seenbutnotmemorised1);

    db->revqueue.limit_new = db->revqueue.idx_new
			     + 1 + db->grade_0_items_at_once;
    if (db->revqueue.limit_new > db->nstats)
	db->revqueue.limit_new = db->nstats;
}

void shiftforgottentonew(carddb_t db)
{
    int i;

    for (i=db->revqueue.num_scheduled - 1; i >= 0; --i) {
	if (db->stats[db->revqueue.q[i]].grade < 2) {
	    swap_revqueue(db, i, db->revqueue.idx_new--);
	    --db->revqueue.num_scheduled;
	}
    }
}

int numscheduled(carddb_t db)
{
    int n = db->revqueue.num_scheduled - db->revqueue.curr;

    if (n < 0)
	return 0;

    return n;
}

int getfirstcard(carddb_t db, card_t* next)
{
    db->revqueue.first = 0;

    if (db->revqueue.num_scheduled > 0) {
	db->revqueue.curr = 0;
	*next = db->revqueue.curr;
	return 1;
    }

    if (db->revqueue.idx_new + 1 < db->revqueue.limit_new) {
	db->revqueue.curr = db->revqueue.idx_new + 1;
	*next = db->revqueue.curr;
	return 1;
    }

    return 0;
}

int getcard(carddb_t db, card_t* next)
{
    if (db->revqueue.first)
	return getfirstcard(db, next);

    if (db->revqueue.curr >= db->revqueue.limit_new)
	return 0;

    if (db->revqueue.curr + 1 < db->revqueue.num_scheduled) {
	*next = ++db->revqueue.curr;
	return 1;
    }

    if (db->revqueue.curr + 1 == db->revqueue.num_scheduled) {
	shiftforgottentonew(db);
	db->revqueue.curr = db->revqueue.idx_new + 1;

    } else if (db->stats[db->revqueue.curr].grade < 2) {
	// shuffle grade 0 cards back into set
	swap_revqueue(db, db->revqueue.curr,
		      randint(db->revqueue.curr, db->revqueue.limit_new - 1));

    } else if (db->stats[db->revqueue.curr].unseen == 1) {
	// shift the limit forward
	++db->revqueue.limit_new;
	++db->revqueue.curr;

    } else {
	++db->revqueue.curr;
    }

    while (db->revqueue.curr < db->revqueue.size
	   && db->stats[db->revqueue.curr].skip
	   && db->stats[db->revqueue.curr].unseen) {
	++db->revqueue.curr;
	++db->revqueue.limit_new;
    }

    if (db->revqueue.limit_new > db->nstats)
	db->revqueue.limit_new = db->nstats;

    if (db->revqueue.curr >= db->revqueue.limit_new)
	return 0;
    
    *next = db->revqueue.curr;
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
void processanswer(carddb_t db, card_t i, int new_grade,
		   long thinking_time_msecs)
{
    stat_t scheduled_interval;
    stat_t actual_interval;
    float new_interval;
    cardstats_t* item = &db->stats[i];
    int noise;

    // Don't schedule inverse or identical questions on the same day.
    if (item->inverse != NO_INVERSE)
	db->stats[item->inverse].skip = 1;

    // Calculate scheduled and actual interval, taking care of corner
    // case when learning ahead on the same day.
    
    scheduled_interval = item->next_rep   - item->last_rep;
    actual_interval    = db->days_since_start - item->last_rep;

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
	    } else if (item->easiness < 1300) {
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
    item->last_rep = db->days_since_start;
    item->next_rep = db->days_since_start + (time_t)new_interval + noise;
    item->unseen   = 0;
    
    if (db->logfile != NULL) {
	// NOTE: the <%d> must be replaced with the id.
	fprintf(db->logfile,
		"R <%hd> %d %1.2f | %d %d %d %d %d | %d %d | %d %d | %1.1f\n",
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
		(float)thinking_time_msecs / 100);
    }
}

void htmlfilename(carddb_t db, card_t i, int answer, char* name)
{
    sprintf(name, "%c%04hx.htm", (answer?'A':'Q'), i);
}

void assertinvariants(carddb_t db)
{
    assert(sizeof(card_t) >= 2);    // bytes
    assert(sizeof(grade_t) >= 1);   // byte
    assert(sizeof(cat_t) >= 1);	    // byte
    assert(sizeof(bool_t) >= 1);    // byte
    assert(sizeof(stat_t) >= 2);    // bytes
    assert(sizeof(time_t) >= 4);    // bytes

    assert(db->revqueue.num_scheduled <= (db->revqueue.idx_new + 1));
    assert(db->revqueue.idx_new <= db->revqueue.limit_new);
    assert(db->revqueue.limit_new <= db->revqueue.size);
    assert((db->revqueue.curr <= db->revqueue.num_scheduled)
	   || ((db->revqueue.curr > db->revqueue.idx_new)
	       && (db->revqueue.curr <= db->revqueue.limit_new)));
}

void debughtmlcsv(carddb_t db, FILE *f, int showqueue)
{
    int i;

    if (showqueue) {
	fprintf(f, "scheduled----------------------\n");
	for (i = 0; i < db->revqueue.num_scheduled; ++i) {
	    fprintf(f,"%3d serial=%3d key=%d\n", i, db->revqueue.q[i], 
			sort_key_interval(db, db->revqueue.q[i]));
	}
	fprintf(f, "new----------------------------\n");
	for (i = db->revqueue.idx_new + 1; i < db->revqueue.size; ++i) {
	    if (i == db->revqueue.limit_new)
		fprintf(f, "--new limit--\n");
	    fprintf(f, "%3d serial=%3d re0=%d re1=%d sn0=%d sn1=%d\n",
		    i, db->revqueue.q[i], 
		    p_rememorise0(db, db->revqueue.q[i]),
		    p_rememorise1(db, db->revqueue.q[i]),
		    p_seenbutnotmemorised0(db, db->revqueue.q[i]),
		    p_seenbutnotmemorised1(db, db->revqueue.q[i]));
	}
    }
    fprintf(f, "-------------------------------\n");
    fprintf(f, "nstats=%hd\n", db->nstats);
    fprintf(f, "days_since_start=%hd\n", db->days_since_start);
    fprintf(f, "revqueue.num_scheduled=%d\n", db->revqueue.num_scheduled);
    fprintf(f, "revqueue.idx_new=%d\n", db->revqueue.idx_new);
    fprintf(f, "revqueue.limit_new=%d\n", db->revqueue.limit_new);
    fprintf(f, "revqueue.curr=%d\n", db->revqueue.curr);
    fprintf(f, "revqueue.first=%d\n", db->revqueue.first);
}

