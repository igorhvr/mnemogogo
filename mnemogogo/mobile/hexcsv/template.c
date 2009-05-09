
#include <stdio.h>
#include <stdlib.h>
#include "hexcsv.h"

/*
    Potential mobile clients:
    * Symbian S60 OS on (mostly) Nokia mobile phones
	- use P.I.P.S to compile hexcsv library
	- rewrite the main function in Symbian C++
	- use the web browser control to display cards
 */

int main(int argc, char** argv)
{
    int grade, numsched, r;
    int done = 0;
    carddb_t db;
    card_t curr;
    char filename[LEN_HTMLFILENAME];
    time_t start_time;
    time_t end_time;

    // TODO: change directory to the import path

    db = loadcarddb(NULL, &r);
    if (r < 0) {
	//TODO: abort with error message:
	errorstr(r);
    }

    buildrevisionqueue(db);

    while (!done && getcard(db, &curr)) {
	numsched = numscheduled(db);
	// TODO: display the number of scheduled cards

	// TODO: display html file:
	start_time = time(NULL);
	htmlfilename(db, curr, 0, filename); // prefix with 'cards/'

	// TODO: wait for 'show answer' key

	// TODO: display html file:
	htmlfilename(db, curr, 1, filename); // prefix with 'cards/'
	
	// TODO: wait for 'grade' key
	end_time = time(NULL);
	grade = 4;
	processanswer(db, curr, grade, (long)(end_time - start_time) * 1000);
    }

    savecarddb(db, NULL);
    freecarddb(db);

    return 0;
}

