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
#ifndef __HTMLCSV_H__
#define __HTMLCSV_H__

#include <stdlib.h>
#include <stdio.h>
#include <time.h>

typedef struct _carddb_t *carddb_t;
typedef unsigned short card_t;

#define ERROR_FILE_NOT_FOUND -1
#define ERROR_MALLOC -2
#define ERROR_CORRUPT_DB -3
#define ERROR_WRITING_DB -4
#define LEN_HTMLFILENAME 10
#define STAT_FORMAT "gr=%1d e=%2.03f r=%4d l=%4d ds=%6d"
// "gr=0 e=00.000 r=0000 l=0000 ds=00000";

#ifdef __cplusplus
extern "C" {
#endif

void write_config(carddb_t, FILE*);

void freecarddb(carddb_t);

/* 10 bytes will be appended to path.
 * The last character should be a path separator '\', or '/'. */
carddb_t loadcarddb(char* path, int *err);
int writecard(carddb_t, FILE*, card_t);
int writecarddb(carddb_t, FILE*);
int savecarddb(carddb_t, char* path);

char* printstats(carddb_t, card_t, char *statstring);
const char* errorstr(int);

void buildrevisionqueue(carddb_t);
int numscheduled(carddb_t);
int daysleft(carddb_t);
int getcard(carddb_t, card_t* next);
void processanswer(carddb_t, card_t item, int new_grade,
		   long thinking_time_secs);
void htmlfilename(carddb_t, card_t, int answer, char *name);
void assertinvariants(carddb_t);
void debughtmlcsv(carddb_t, FILE*, int showqueue);

#ifdef __cplusplus
}
#endif

#endif
