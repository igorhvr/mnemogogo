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

/*
 *  Current limitations:
 *  - thinking_time is not yet implemented
 */

#include <stdlib.h>
#include <stdio.h>

typedef unsigned short card_t;

#define ERROR_FILE_NOT_FOUND -1
#define ERROR_MALLOC -2
#define ERROR_CORRUPT_DB -3
#define ERROR_WRITING_DB -4

void write_config(FILE*);

void freecarddb(void);

int loadcarddb(char* path);
int writecard(FILE* f, card_t i);
int writecarddb(FILE*);
int savecarddb(char* path);

char* printstats(card_t);
const char* errorstr(int);

void buildrevisionqueue(void);
int numscheduled(void);
int getcard(card_t* next);
void processanswer(card_t item, int new_grade);
char* htmlfilename(card_t, int answer);
void assertinvariants(void);
void debughtmlcsv(FILE*, int showqueue);

#endif
