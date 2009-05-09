.SUFFIXES: .java .class

CC=cc

WTKPATH=/usr/local/sun-wtk
CLASSPATH=../../..
JAVAC=javac -bootclasspath \
      $(WTKPATH)/lib/cldcapi11.jar:$(WTKPATH)/lib/midpapi20.jar:$(WTKPATH)/lib/jsr75.jar \
	-classpath $(CLASSPATH)

# C

hexcsv.o: hexcsv.h hexcsv.c
	$(CC) -c hexcsv.c

all: test_loadwrite test_checkstats template

test_loadwrite: test_loadwrite.c hexcsv.o
	$(CC) -o test_loadwrite test_loadwrite.c hexcsv.o

test_checkstats: test_checkstats.c hexcsv.o
	$(CC) -o test_checkstats test_checkstats.c hexcsv.o

template: template.c hexcsv.o
	$(CC) -o template template.c hexcsv.o

# Java

java: HexCsv.class FindCardDir.class LoadedCard.class
HexCsv.class: HexCsv.java Card.class Config.class RevQueue.class StatIO.class \
	CardList.class
Card.class: Card.java StatIO.class CardList.class
Config.class: Config.java
RevQueue.class: RevQueue.java Config.class StatIO.class Card.class Progress.class
StatIO.class: StatIO.java
CardList.class: CardList.java
FindCardDir.class: FindCardDir.java Progress.class
Progress.class: Progress.java
LoadedCard.class: LoadedCard.java

# General

clean:
	-@rm hexcsv.o *.core
	-@rm test_loadwrite test_checkstats template
	-@rm *.class

.java.class:
	$(JAVAC) $<

