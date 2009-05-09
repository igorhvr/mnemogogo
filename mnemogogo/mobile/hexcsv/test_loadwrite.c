#include <stdio.h>
#include <stdlib.h>
#include "hexcsv.h"

int main(int argc, char** argv)
{
    int r;
    carddb_t db;

    if (argc != 2) {
	fprintf(stderr, "please specify a filename\n");
	return -1;
    }

    db = loadcarddb(argv[1], &r);
    if (r < 0) {
	fprintf(stderr, "error: %s\n", errorstr(r));
	return r;
    }
    printf("%d\n", r);
    writecarddb(db, stdout);

    freecarddb(db);

    return 0;
}

