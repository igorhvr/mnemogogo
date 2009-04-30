.SUFFIXES: .java .class

CC=cc

WTKPATH=/usr/local/sun-wtk
JAVAC=javac -bootclasspath \
	$(WTKPATH)/lib/cldcapi11.jar:$(WTKPATH)/lib/midpapi20.jar

# C

htmlcsv.o: htmlcsv.h htmlcsv.c
	$(CC) -c htmlcsv.c

all: test_loadwrite test_checkstats template

test_loadwrite: test_loadwrite.c htmlcsv.o
	$(CC) -o test_loadwrite test_loadwrite.c htmlcsv.o

test_checkstats: test_checkstats.c htmlcsv.o
	$(CC) -o test_checkstats test_checkstats.c htmlcsv.o

template: template.c htmlcsv.o
	$(CC) -o template template.c htmlcsv.o

# Java

java: HtmlCsv.class
HtmlCsv.class: HtmlCsv.java CardStats.java Config.java RevQueue.java StatIO.java
CardStats.class: CardStats.java StatIO.java
Config.class: Config.java
RevQueue.class: RevQueue.java Config.java StatIO.java CardStats.java
StatIO.class: StatIO.java

# General

clean:
	-@rm htmlcsv.o *.core
	-@rm test_loadwrite test_checkstats template

.java.class:
	$(JAVAC) $<

