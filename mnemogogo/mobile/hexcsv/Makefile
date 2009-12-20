.SUFFIXES: .java .class

WTKPATH=/opt/WTK2.5.2
CLASSPATH=../../..
JAVAC=javac -bootclasspath \
      $(WTKPATH)/lib/cldcapi11.jar:$(WTKPATH)/lib/midpapi20.jar:$(WTKPATH)/lib/jsr75.jar \
	-classpath $(CLASSPATH)

# Java

java: HexCsv.class FindCardDir.class
HexCsv.class: HexCsv.java Card.class Config.class RevQueue.class StatIO.class \
	CardList.class CardData.class
Card.class: Card.java StatIO.class CardList.class
Config.class: Config.java
RevQueue.class: RevQueue.java Config.class StatIO.class Card.class Progress.class
StatIO.class: StatIO.java
CardList.class: CardList.java
FindCardDir.class: FindCardDir.java Progress.class
Progress.class: Progress.java
CardData.class: CardData.java Progress.class

# General

clean:
	-@rm *.class

.java.class:
	$(JAVAC) $<

