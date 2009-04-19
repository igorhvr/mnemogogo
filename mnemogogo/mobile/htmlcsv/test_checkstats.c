#include <stdio.h>
#include <stdlib.h>
#include "htmlcsv.h"

#define MAX_ID_LEN 20
#define MAX_DB_SIZE 10000

char ids[MAX_DB_SIZE][MAX_ID_LEN];
int max_id;
int grades[MAX_DB_SIZE];

void chomp(char* str)
{
    while (*str != '\0' && *str != '\n')
	++str;

    *str = '\0';
}

void read_ids(void)
{
    int i = 0;
    FILE* f = fopen("ids", "r");

    while (fgets(ids[i], MAX_ID_LEN, f)) {
	chomp(ids[i]);
	grades[i] = -1;
	++i;
    }

    max_id = i;
    fclose(f);
}

int id_to_serial(char* id)
{
    int i;

    for (i=0; i < max_id; ++i)
	if (strcmp(ids[i], id) == 0)
	    return i;

    return -1;
}

void read_grades(void)
{
    int i = 0;
    FILE* f = fopen("grades", "r");
    char line[BUFSIZ];
    char id[MAX_ID_LEN];
    int serial;
    int grade;

    while (fgets(line, BUFSIZ, f)) {
	sscanf(line, "%s %d", &id, &grade);
	serial = id_to_serial(id);
	if (serial > 0)
	    grades[serial] = grade;
    }

    fclose(f);
}

int main(int argc, char** argv)
{
    int r;
    card_t curr;

    char* srcpath = argv[1];
    char* dstpath = argv[1];

    if (argc < 2) {
	fprintf(stderr, "please specify a sync path\n");
	return -1;
    }

    if (argc > 2)
	dstpath = argv[1];

    r = loadcarddb(srcpath);
    if (r < 0) {
	fprintf(stderr, "error: %s\n", errorstr(r));
	return r;
    }
    assertinvariants();

    while (getcard(&curr)) {
	assertinvariants();

	if (grades[curr] == -1) {
	    printf("no grade for card %s\n", ids[(int)curr]);

	} else {
	    processanswer(curr, grades[curr]);
	    printf("%s: ", ids[(int)curr]);
	    writecard(stdout, curr);
	}
    }

    assertinvariants();
    savecarddb(dstpath);
    freecarddb();
    return 0;
}

