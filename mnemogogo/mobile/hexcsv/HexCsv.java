/*
 * Copyright (C) 2009 Timothy Bourke
 * 
 * This program is free software; you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by the Free
 * Software Foundation; either version 2 of the License, or (at your option)
 * any later version.
 * 
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
 * or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
 * for more details.
 * 
 * You should have received a copy of the GNU General Public License along
 * with this program; if not, write to the Free Software Foundation, Inc., 59
 * Temple Place, Suite 330, Boston, MA 02111-1307 USA
 */

package mnemogogo.mobile.hexcsv;

import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.DataInputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.IOException;
import java.io.UnsupportedEncodingException;
import java.util.Date;
import java.util.Calendar;
import java.util.TimeZone;

abstract class HexCsv
    implements CardList, CardDataSet
{
    private Card cards[];
    private RevQueue q;
    private int days_left;
    private Config config;
    private Progress progress;

    private boolean specify_encoding;
    private boolean allow_skip_categories;

    public long days_since_start;
    public OutputStreamWriter logfile;
    public String categories[];
    public boolean skip_categories[];

    public int cards_to_load = 50;

    public static final String ascii = "US-ASCII";
    public static final String utf8 = "UTF-8";

    public static final String readingStatsText = "Loading statistics";
    public static final String writingStatsText = "Writing statistics";
    public static final String loadingCardsText = "Loading cards";

    private StringBuffer pathbuf;
    private int path_len;

    public HexCsv(String path, Progress prog,
                  boolean specify_encoding,
                  boolean allow_skip_categories)
        throws Exception, IOException
    {
        this.specify_encoding = specify_encoding;
        this.allow_skip_categories = allow_skip_categories;

        path_len = path.length();
        pathbuf = new StringBuffer(path_len + 20);
        pathbuf.append(path);

        progress = prog;

        readConfig(pathbuf);

        days_left = daysLeft(config.lastDay());
        days_since_start = daysSinceStart(config.startDay());

        truncatePathBuf();
        readCategories(pathbuf);

        truncatePathBuf();
        readCategorySkips(pathbuf);

        truncatePathBuf();
        readCards(pathbuf);

        if (config.logging()) {
            truncatePathBuf();
            pathbuf.append("PRELOG");
            openLogFile(pathbuf.toString());
        }
    }

    void truncatePathBuf()
    {
        pathbuf.delete(path_len, pathbuf.length());
    }

    private void openLogFile(String filepath)
    {
        try {
            OutputStream outs = openAppend(filepath);
            if (specify_encoding) {
                try {
                    logfile = new OutputStreamWriter(outs, ascii);
                } catch (UnsupportedEncodingException e) {
                    logfile = new OutputStreamWriter(outs);
                }
            } else {
                logfile = new OutputStreamWriter(outs);
            }
        } catch (Exception e) {
            logfile = null;
        }
    }

    public String getCategory(int n)
    {
        if (0 <= n && n < categories.length) {
            return categories[n];
        } else {
            return null;
        }
    }

    public boolean skipCategory(int n)
    {
        if (0 <= n && n < categories.length) {
            return skip_categories[n];
        } else {
            return false;
        }
    }

    public void setSkipCategory(int n, boolean skip)
    {
        if (0 <= n && n < categories.length) {
            skip_categories[n] = skip;
        }
    }

    public int numCategories()
    {
        return categories.length;
    }

    public Card getCard()
    {
        return q.getCard();
    }

    public Card getCard(int serial)
    {
        if (0 <= serial && serial < cards.length) {
            return cards[serial];
        } else {
            return null;
        }
    }

    private void readConfig(StringBuffer path)
        throws IOException
    {
        InputStream is = openIn(path.append("CONFIG").toString());
        InputStreamReader in;

        if (specify_encoding) {
            try {
                in = new InputStreamReader(is, ascii);
            } catch (UnsupportedEncodingException e) {
                in = new InputStreamReader(is);
            }
        } else {
            in = new InputStreamReader(is);
        }

        config = new Config(in);
        in.close();
    }

    public long nowInDays()
    {
        Date now = new Date(); // UTC (millisecs since 01/01/1970, 00:00:00 GMT)

        // hours since epoch in UTC
        long hours = now.getTime() / 3600000;

        // offset from UTC to local in hours
        Calendar cal = Calendar.getInstance();
        TimeZone tz = cal.getTimeZone();
        long tzoff = tz.getRawOffset() / 3600000;

        // e.g.
        // for day_starts_at = 3 (0300 local time)
        // and UTC +8
        // the next day should start at UTC 1900
        // (not at UTC 0000)
        // because 1900 + 8 - 3 = 0000

        return (hours + tzoff - config.dayStartsAt()) / 24;
    }

    private long daysSinceStart(long start_days)
    {
        long now_days = nowInDays();
        return now_days - start_days;
    }

    public int daysLeft()
    {
        return days_left;
    }

    private int daysLeft(long last_day)
    {
        if (last_day < 0) {
            return (int)-last_day;
        }
        return (int)(last_day - nowInDays());
    }

    private void readCards(StringBuffer path)
        throws IOException
    {
        InputStream is = openIn(path.append("STATS.CSV").toString());
        InputStreamReader in;

        if (specify_encoding) {
            try {
                in = new InputStreamReader(is, ascii);
            } catch (UnsupportedEncodingException e) {
                in = new InputStreamReader(is);
            }
        } else {
            in = new InputStreamReader(is);
        }

        int ncards = StatIO.readInt(in);
        progress.startOperation(ncards * 3, readingStatsText);

        cards = new Card[ncards];
        Card.cardlookup = this;

        for (int i=0; i < ncards; ++i) {
            cards[i] = new Card(in, i);
            if (i % 10 == 0) {
                progress.updateOperation(10);
            }
        }
        progress.stopOperation();

        in.close();

        q = new RevQueue(ncards, days_since_start, config, progress, days_left);
        q.buildRevisionQueue(cards, false);
    }

    public void rebuildQueue()
    {
        q.buildRevisionQueue(cards, false);
    }
    
    public void learnAhead()
    {
        q.buildRevisionQueue(cards, true);
    }

    public boolean canLearnAhead()
    {
        return q.canLearnAhead(cards);
    }

    public void writeCards(StringBuffer path, String name, Progress progress)
        throws IOException
    {
        OutputStream os = openOut(path.append(name).toString());
        OutputStreamWriter out;

        if (specify_encoding) {
            try {
                out = new OutputStreamWriter(os, ascii);
            } catch (UnsupportedEncodingException e) {
                out = new OutputStreamWriter(os);
            }
        } else {
            out = new OutputStreamWriter(os);
        }

        StatIO.writeInt(out, cards.length, "\n");

        if (progress != null) {
            progress.startOperation(cards.length, writingStatsText);
        }
        for (int i=0; i < cards.length; ++i) {
            cards[i].writeCard(out);

            if (i % 10 == 0 && progress != null) {
                progress.updateOperation(10);
            }
        }
        if (progress != null) {
            progress.stopOperation();
        }

        out.flush();
        out.close();
    }

    public void writeCards(StringBuffer path, Progress progress)
        throws IOException
    {
        writeCards(path, "STATS.CSV", progress);
    }

    public void backupCards(StringBuffer path, Progress progress)
        throws IOException
    {
        writeCards(path, "STATS.BKP", progress);
    }

    private void readCategorySkips(StringBuffer path)
    {
        int n = categories.length;

        skip_categories = new boolean[n];
        for(int i=0; i < n; ++i) {
            skip_categories[i] = false;
        }

        if (!allow_skip_categories) {
            return;
        }

        try {
            InputStream is = openIn(path.append("SKIPCATS").toString());
            InputStreamReader in;

            if (specify_encoding) {
                try {
                    in = new InputStreamReader(is, utf8);
                } catch (UnsupportedEncodingException e) {
                    in = new InputStreamReader(is);
                }
            } else {
                in = new InputStreamReader(is);
            }

            String cat = StatIO.readLine(in);
            while (!cat.equals("")) {
                for (int i=0; i < n; ++i) {
                    if (cat.equals(categories[i])) {
                        skip_categories[i] = true;
                        break;
                    }
                }
                cat = StatIO.readLine(in);
            }

            in.close();
        } catch (Exception e) { }
    }

    public void writeCategorySkips(StringBuffer path)
    {
        if (!allow_skip_categories) {
            return;
        }

        try {
            OutputStream os = openOut(path.append("SKIPCATS").toString());
            OutputStreamWriter out;

            if (specify_encoding) {
                try {
                    out = new OutputStreamWriter(os, utf8);
                } catch (UnsupportedEncodingException e) {
                    out = new OutputStreamWriter(os);
                }
            } else {
                out = new OutputStreamWriter(os);
            }

            for (int i=0; i < categories.length; ++i) {
                if (skip_categories[i]) {
                    out.write(categories[i]);
                    out.write('\n');
                }
            }

            out.flush();
            out.close();
        } catch (Exception e) { }
    }

    private void readCategories(StringBuffer path)
        throws IOException
    {
        InputStream is = openIn(path.append("CATS").toString());
        InputStreamReader in;

        if (specify_encoding) {
            try {
                in = new InputStreamReader(is, utf8);
            } catch (UnsupportedEncodingException e) {
                in = new InputStreamReader(is);
            }
        } else {
            in = new InputStreamReader(is);
        }

        int n = StatIO.readInt(in);
        StatIO.readInt(in); // skip the size in bytes

        categories = new String[n];
        for (int i=0; i < n; ++i) {
            categories[i] = StatIO.readLine(in);
        }

        in.close();
    }

    public void setCardData(int serial, String question, String answer,
                boolean overlay)
    {
        cards[serial].setOverlay(overlay);
        cards[serial].setQuestion(question);
        cards[serial].setAnswer(answer);
    }

    public boolean cardDataNeeded(int serial)
    {
        return ((cards[serial].isDueForRetentionRep(days_since_start)
                 || cards[serial].isDueForAcquisitionRep()
                 || (q.isLearningAhead()
                     && cards[serial].qualifiesForLearnAhead(days_since_start)))
                && q.isScheduledSoon(serial, cards_to_load));
    }

    public void setProgress(Progress new_progress)
    {
        progress = new_progress;
    }

    private void readCardText(StringBuffer path)
        throws IOException
    {
        DataInputStream is = openDataIn(path.append("CARDS").toString());

        // the new object is not needed, rather just that its constructor
        // updates this object.
        new CardData(is, progress, this);
        is.close();
    }

    public void loadCardData()
        throws IOException
    {
        // clear any existing questions and answers
        for (int i=0; i < cards.length; ++i) {
            cards[i].setQuestion(null);
            cards[i].setAnswer(null);
        }

        // load them again
        truncatePathBuf();
        progress.startOperation(cards.length, loadingCardsText);
        readCardText(pathbuf);
        progress.stopOperation();
    }

    public int numScheduled()
    {
        return q.numScheduled();
    }

    public void addToFutureSchedule(Card card)
    {
        q.addToFutureSchedule(card);
    }

    public void removeFromFutureSchedule(Card card)
    {
        q.removeFromFutureSchedule(card);
    }

    public int[] getFutureSchedule()
    {
        return q.getFutureSchedule();
    }

    public String toString()
    {
        return q.toString();
    }

    public void dumpCards()
    {
        System.out.println("----Cards:");
        for (int i=0; i < cards.length; ++i) {
            System.out.print("  ");
            System.out.println(cards[i].toString());
        }
    }

    public void close()
    {
        if (logfile != null) {
            try {
                logfile.close();
            } catch (IOException e) { }
            logfile = null;
        }
    }

    public void reopen(String path)
    {
        if (logfile == null && config.logging()) {
            pathbuf = new StringBuffer(path);
            pathbuf.append("PRELOG");
            openLogFile(pathbuf.toString());
        }
    }

    abstract protected OutputStream openAppend(String path)
        throws IOException;
    abstract protected OutputStream openOut(String path)
        throws IOException;
    abstract protected InputStream openIn(String path)
        throws IOException;
    abstract protected DataInputStream openDataIn(String path)
        throws IOException;
}

