.SUFFIXES: .java .class

CC=cc

WTKPATH=/usr/local/sun-wtk
CLASSPATH=../../..
JAVAC=javac -bootclasspath \
      $(WTKPATH)/lib/cldcapi11.jar:$(WTKPATH)/lib/midpapi20.jar:$(WTKPATH)/lib/jsr75.jar \
	-classpath $(CLASSPATH)

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

java: HtmlCsv.class FindCardDir.class LoadedCard.class
HtmlCsv.class: HtmlCsv.java Card.class Config.class RevQueue.class StatIO.class \
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
	-@rm htmlcsv.o *.core
	-@rm test_loadwrite test_checkstats template
	-@rm *.class

.java.class:
	$(JAVAC) $<

