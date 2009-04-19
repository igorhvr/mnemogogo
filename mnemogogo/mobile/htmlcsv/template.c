
#include <stdio.h>
#include <stdlib.h>
#include "htmlcsv.h"

/*
    Potential mobile clients:
    * Symbian S60 OS on (mostly) Nokia mobile phones
	- use P.I.P.S to compile htmlcsv library
	- rewrite the main function in Sybmian C++
	- use the web browser control to display cards
 */

int main(int argc, char** argv)
{
    int grade, numsched, r;
    int done = 0;
    card_t curr;

    // TODO: change directory to the import path

    r = loadcarddb(NULL);
    if (r < 0) {
	//TODO: abort with error message:
	errorstr(r);
    }

    while (!done && getcard(&curr)) {
	numsched = numscheduled();
	// TODO: display the number of scheduled cards

	// TODO: display html file:
	htmlfilename(curr); // prefix with 'cards/'

	// TODO: wait for 'show answer' key
	if (hasoverlay(curr)) {
	    // TODO: set htmldoc.body.q.style = 'display: none'
	}
	// TODO: set htmldoc.body.a.style = 'display: block'
	
	// TODO: wait for 'grade' key
	grade = 4;
	processanswer(curr, grade);
    }

    savecarddb(NULL);
    freecarddb();

    return 0;
}

