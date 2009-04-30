/*
 * Copyright (c) 2009 Timothy Bourke
 * All rights reserved.
 *
 * This program is free software; you can redistribute it and/or modify it
 * under the terms of the "BSD License" which is distributed with the
 * software in the file ../LICENSE.
 *
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the BSD
 * License for more details.
 */
/*
 * Certain routines Copyright (c) Peter Bienstman <Peter.Bienstman@UGent.be>
 */

import java.lang.*;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.IOException;
import java.util.Date;
import javax.microedition.io.Connector;

public class HtmlCsv
{
    private CardStats stats[];
    private RevQueue q;
    private OutputStreamWriter logfile;
    private long days_since_start;
    private Config config;

    public String categories[];

    private static String ascii = "ASCII";
    private static String utf8 = "UTF-8";

    HtmlCsv(String path)
	throws IOException
    {
	long start_time;
	long adjusted_now;
	int num_cards;
	int path_len = path.length();
	StringBuffer p = new StringBuffer(path_len + 20);
	p.append(path);

	readConfig(p);

	p.delete(path_len, p.length());
	calculateDaysSinceStart(p);

	p.delete(path_len, p.length());
	readStats(p);

	p.delete(path_len, p.length());
	readCategories(p);

	if (config.logging()) {
	    // TODO: check that this really appends?
	    logfile = new OutputStreamWriter(
		Connector.openOutputStream(
		    p.append("prelog").append(";type=a").toString()),
		ascii);
	}

	q = new RevQueue(stats.length, days_since_start, config);
	q.updateInverses(stats);
    }

    private void readConfig(StringBuffer path)
	throws IOException
    {
	InputStreamReader in = new InputStreamReader(
		Connector.openInputStream(path.append("config").toString()),
		ascii);
	config = new Config(in);
	in.close();
    }

    private void calculateDaysSinceStart(StringBuffer path)
	throws IOException
    {

	InputStreamReader in = new InputStreamReader(
	    Connector.openInputStream(path.append("start_time").toString()),
	    ascii);
	long start_time = StatIO.readLong(in);
	in.close();

	Date now = new Date();
	long adjusted_now = (now.getTime() / 1000) -
				((long)config.dayStartsAt() * 3600);
	days_since_start = (adjusted_now - start_time) / 86400;
    }

    private void readStats(StringBuffer path)
	throws IOException
    {
	InputStreamReader in = new InputStreamReader(
	    Connector.openInputStream(path.append("stats.csv").toString()),
	    ascii);

	int nstats = StatIO.readInt(in);

	stats = new CardStats[nstats];
	q = new RevQueue(nstats, days_since_start, config);

	for (int i=0; i < nstats; ++i) {
	    stats[i] = new CardStats(in, i);
	}

	in.close();
    }

    public void writeCards(StringBuffer path)
	throws IOException
    {
	OutputStreamWriter out = new OutputStreamWriter(
	    Connector.openOutputStream(path.append("stats.csv").toString()),
	    ascii);

	StatIO.writeInt(out, stats.length, "\n");

	for (int i=0; i < stats.length; ++i) {
	    stats[i].writeCard(out);
	}

	out.close();
    }

    private void readCategories(StringBuffer path)
	throws IOException
    {
	InputStreamReader in = new InputStreamReader(
	    Connector.openInputStream(path.append("categories").toString()),
	    utf8);

	int n = StatIO.readInt(in);
	int bytesize = StatIO.readInt(in);

	categories = new String[n];
	for (int i=0; i < n; ++i) {
	    categories[i] = StatIO.readLine(in);
	}

	in.close();
    }
}

