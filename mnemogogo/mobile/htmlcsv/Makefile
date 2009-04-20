CC=cc

htmlcsv.o: htmlcsv.h htmlcsv.c
	$(CC) -c htmlcsv.c

all: test_loadwrite test_checkstats template

test_loadwrite: test_loadwrite.c htmlcsv.o
	$(CC) -o test_loadwrite test_loadwrite.c htmlcsv.o

test_checkstats: test_checkstats.c htmlcsv.o
	$(CC) -o test_checkstats test_checkstats.c htmlcsv.o

template: template.c htmlcsv.o
	$(CC) -o template template.c htmlcsv.o

clean:
	-@rm htmlcsv.o *.core
	-@rm test_loadwrite test_checkstats template

