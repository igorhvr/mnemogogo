/*
 * Copyright (c) 2009 Timothy Bourke
 * All rights reserved.
 *
 * This program is free software; you can redistribute it and/or modify it
 * under the terms of the "BSD License" which is distributed with the
 * software in the file ../../LICENSE.
 *
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the BSD
 * License for more details.
 */

package mnemogogo.mobile.hexcsv;

import java.lang.*;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.DataInputStream;
import java.io.IOException;
import java.util.Date;
import java.util.Calendar;
import java.util.TimeZone;
import javax.microedition.io.Connector;
import java.io.OutputStream;
import javax.microedition.io.file.FileConnection; /*JSR-75*/

public class HexCsv
    implements CardList, CardDataSet
{
    private Card cards[];
    private RevQueue q;
    private int days_left;
    private Config config;
    private Progress progress;

    public long days_since_start;
    public OutputStreamWriter logfile;
    public String categories[];

    public static String ascii = "US-ASCII";
    public static String utf8 = "UTF-8";

    public HexCsv(String path, Progress prog)
	throws IOException
    {
	String v;
	long start_time;
	long adjusted_now;
	int num_cards;
	int path_len = path.length();
	StringBuffer p = new StringBuffer(path_len + 20);
	p.append(path);

	progress = prog;

	readConfig(p);

	v = config.getString("last_day");
	days_left = daysLeft(Long.parseLong(v));

	v = config.getString("start_time");
	days_since_start = daysSinceStart(Long.parseLong(v));

	p.delete(path_len, p.length());
	readCards(p);

	p.delete(path_len, p.length());
	readCardText(p);

	p.delete(path_len, p.length());
	readCategories(p);

	if (config.logging()) {
	    p.delete(path_len, p.length());
	    p.append("PRELOG");

	    FileConnection file =
		(FileConnection)Connector.open(p.toString());
	    OutputStream outs = file.openOutputStream(file.fileSize());
	    logfile = new OutputStreamWriter(outs, ascii);
	}
    }

    public String getCategory(int n) {
	if (0 <= n && n < categories.length) {
	    return categories[n];
	} else {
	    return null;
	}
    }

    public Card getCard(int serial) {
	if (0 < serial && serial < cards.length) {
	    return cards[serial];
	} else {
	    return null;
	}
    }

    private void readConfig(StringBuffer path)
	throws IOException
    {
	InputStreamReader in = new InputStreamReader(
		Connector.openInputStream(path.append("CONFIG").toString()),
		ascii);
	config = new Config(in);
	in.close();
    }

    private long daysSinceStart(long start_time)
    {
	Date now = new Date();
	long adjusted_now = (now.getTime() / 1000) -
				(config.dayStartsAt() * 3600);
	return (adjusted_now - start_time) / 86400;
    }

    public int daysLeft() {
	return days_left;
    }

    private int daysLeft(long last_day)
    {
	Date now = new Date();

	// hours since epoch in UTC
	long hours = now.getTime() / 3600000;
	Calendar cal = Calendar.getInstance();
	TimeZone tz = cal.getTimeZone();
	long tzoff = tz.getRawOffset() / 3600000;
	System.out.print("tzoff="); // XXX
	System.out.println(tzoff); // XXX

	return (int)(last_day - ((hours - tzoff - config.dayStartsAt()) / 24));
    }

    private void readCards(StringBuffer path)
	throws IOException
    {
	InputStreamReader in = new InputStreamReader(
	    Connector.openInputStream(path.append("STATS.CSV").toString()),
	    ascii);

	int ncards = StatIO.readInt(in);
	progress.startOperation(ncards * 3);

	cards = new Card[ncards];

	for (int i=0; i < ncards; ++i) {
	    cards[i] = new Card(this, in, i);
	    if (i % 10 == 0) {
		progress.updateOperation(10);
	    }
	}

	in.close();

	q = new RevQueue(ncards, days_since_start, config, progress, days_left);
	q.buildRevisionQueue(cards);
    }

    public void writeCards(StringBuffer path, Progress progress)
	throws IOException
    {
	OutputStreamWriter out = new OutputStreamWriter(
	    Connector.openOutputStream(path.append("STATS.CSV").toString()),
	    ascii);

	StatIO.writeInt(out, cards.length, "\n");

	progress.startOperation(cards.length);
	for (int i=0; i < cards.length; ++i) {
	    cards[i].writeCard(out);

	    if (i % 10 == 0 && progress != null) {
		progress.updateOperation(10);
	    }
	}

	out.close();
    }

    private void readCategories(StringBuffer path)
	throws IOException
    {
	InputStreamReader in = new InputStreamReader(
	    Connector.openInputStream(path.append("CATS").toString()), utf8);

	int n = StatIO.readInt(in);
	int bytesize = StatIO.readInt(in);

	categories = new String[n];
	for (int i=0; i < n; ++i) {
	    categories[i] = StatIO.readLine(in);
	}

	in.close();
    }

    public void setCardData(int serial, String question, String answer,
		boolean overlay)
    {
	cards[serial].overlay = overlay;
	cards[serial].question = question;
	cards[serial].answer = answer;
    }

    public boolean cardDataNeeded(int serial)
    {
	return (cards[serial].isDueForRetentionRep(days_since_start)
		|| cards[serial].isDueForAcquisitionRep());
    }

    private void readCardText(StringBuffer path)
	throws IOException
    {
	DataInputStream is = Connector.openDataInputStream(
	    path.append("CARDS").toString());

	CardData carddata = new CardData(is, progress, this);

	is.close();
    }

    public int numScheduled() {
	return q.numScheduled();
    }

    public Card getCard() {
	return q.getCard();
    }

    public void updateFutureSchedule(Card card) {
	q.updateFutureSchedule(card);
    }

    public int[] getFutureSchedule() {
	return q.futureSchedule;
    }

    public String toString() {
	return q.toString();
    }

    public void dumpCards() {
	System.out.println("----Cards:");
	for (int i=0; i < cards.length; ++i) {
	    System.out.print("  ");
	    System.out.println(cards[i].toString());
	}
    }

    public void close() {
	if (logfile != null) {
	    try {
		logfile.close();
	    } catch (IOException e) {}
	    logfile = null;
	}
    }
}

