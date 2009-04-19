#include <stdio.h>
#include <stdlib.h>
#include "htmlcsv.h"

int main(int argc, char** argv)
{
    int r;

    if (argc != 2) {
	fprintf(stderr, "please specify a filename\n");
	return -1;
    }

    r = loadcarddb(argv[1]);
    if (r < 0) {
	fprintf(stderr, "error: %s\n", errorstr(r));
	return r;
    }
    printf("%d\n", r);
    writecarddb(stdout);

    freecarddb();

    return 0;
}

