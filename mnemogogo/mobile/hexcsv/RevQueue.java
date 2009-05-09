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
/*
 * Certain routines Copyright (c) Peter Bienstman <Peter.Bienstman@UGent.be>
 */

package mnemogogo.mobile.hexcsv;

import java.lang.*;
import java.util.Random;

class RevQueue {
    private Card q[];

    int num_scheduled = 0;
    int idx_new;
    int limit_new;

    int curr = 0;
    boolean first = true;
    Random rand = new Random();

    long days_since_start = 0;
    Config config;

    RevQueue(int size, long days, Config c) {
	q = new Card[size];
	idx_new = size - 1;
	limit_new = size;
	days_since_start = days;
	config = c;
    }

    private void swap(int i, int j)
    {
	Card tmp = q[i];
	q[i] = q[j];
	q[j] = tmp;
    }

    // insertion sort: linear when already ordered, won't blow the stack
    // if too slow: implement shell sort
    private void sortScheduled(Progress progress)
    {
	int i, j;
	Card c;
	long key;

	for (i=1; i < num_scheduled; ++i) {
	    c = q[i];
	    key = c.sortKeyInterval();

	    for (j=i-1; j >= 0 && q[j].sortKeyInterval() > key; --j) {
		q[j + 1] = q[j];
	    }
	    q[j + 1] = c;

	    if (i % 10 == 0 && progress != null) {
		progress.updateOperation(10);
	    }
	}
    }

    private void shuffle(int first, int max)
    {
	for (int i=first; i < max; ++i) {
	    swap(i, rand.nextInt(max - first) + first);
	}
    }

    private int clusterRememorise0(int hd, int max)
    {
	for (int i=hd; i < max; ++i) {
	    if (q[i].rememorise0()) {
		swap(i, hd++);
	    }
	}
	return hd;
    }

    private int clusterRememorise1(int hd, int max)
    {
	for (int i=hd; i < max; ++i) {
	    if (q[i].rememorise1()) {
		swap(i, hd++);
	    }
	}
	return hd;
    }

    private int clusterSeenButNotMemorised0(int hd, int max)
    {
	for (int i=hd; i < max; ++i) {
	    if (q[i].seenButNotMemorised0()) {
		swap(i, hd++);
	    }
	}
	return hd;
    }

    private int clusterSeenButNotMemorised1(int hd, int max)
    {
	for (int i=hd; i < max; ++i) {
	    if (q[i].seenButNotMemorised1()) {
		swap(i, hd++);
	    }
	}
	return hd;
    }

    // Adapted directly from Peter Bienstman's Mnemosyne 1.x
    public void buildRevisionQueue(Card[] cards, Progress progress)
    {
	// form two queues:
	//	    cards scheduled for today upward from 0
	//	    wrong and unmemorised cards downward from revqueue.size
	
	num_scheduled = 0;
	idx_new = q.length - 1;
	
	for (int i=0; i < cards.length; ++i) {
	    if (cards[i].isDueForRetentionRep(days_since_start)) {
		q[num_scheduled++] = cards[i];

	    } else if (cards[i].isDueForAcquisitionRep()) {
		q[idx_new--] = cards[i];
	    }

	    if (i % 10 == 0 && progress != null) {
		progress.updateOperation(10);
	    }
	}

	if (config.sorting()) {
	    sortScheduled(progress);
	} else {
	    shuffle(0, num_scheduled);
	}
	shuffle(idx_new + 1, q.length);


	int hd = idx_new + 1;
	hd = clusterRememorise0(hd, q.length);
	if (progress != null) {
	    progress.updateOperation(hd / 10);
	}
	hd = clusterRememorise1(hd, q.length);
	if (progress != null) {
	    progress.updateOperation(hd / 10);
	}
	hd = clusterSeenButNotMemorised0(hd, q.length);
	if (progress != null) {
	    progress.updateOperation(hd / 10);
	}
	hd = clusterSeenButNotMemorised1(hd, q.length);
	if (progress != null) {
	    progress.updateOperation(hd / 10);
	}

	limit_new = idx_new + 1 + config.grade0ItemsAtOnce();
	limit_new = Math.min(limit_new, q.length);
    }

    private void shiftForgottenToNew()
    {
	for (int i=num_scheduled - 1; i >= 0; --i) {
	    if (q[i].grade < 2) {
		swap(i, idx_new--);
		--num_scheduled;
	    }
	}
    }

    public int numScheduled()
    {
	return num_scheduled - curr;
    }

    public Card getFirstCard()
    {
	first = false;

	if (num_scheduled > 0) {
	    curr = 0;
	    return q[curr];
	}

	if (idx_new + 1 < limit_new) {
	    curr = idx_new + 1;
	    return q[curr];
	}

	return null;
    }

    public Card getCard()
    {
	if (first) {
	    return getFirstCard();
	}

	if (curr >= limit_new) {
	    return null;
	}

	if (curr + 1 < num_scheduled) {
	    return q[++curr];
	}

	if (curr + 1 == num_scheduled) {
	    shiftForgottenToNew();
	    curr = idx_new + 1;

	} else if (q[curr].grade < 2) {
	    // shuffle grade 0 and 1 cards back into set
	    swap(curr, rand.nextInt(limit_new - curr) + curr);

	} else if (q[curr].unseen) {
	    // shift the limit forward
	    ++limit_new;
	    ++curr;

	} else {
	    ++curr;
	}

	while (curr < q.length && q[curr].skip && q[curr].unseen) {
	    ++curr;
	    ++limit_new;
	}

	limit_new = Math.max(limit_new, q.length);

	if (curr >= limit_new) {
	    return null;
	}
	
	return q[curr];
    }

    public String toString() {
	StringBuffer r = new StringBuffer();

	r.append("scheduled----------------------\n");
	for (int i=0; i < num_scheduled; ++i) {
	    r.append(i);
	    r.append(" serial=");
	    r.append(q[i].serial);
	    r.append(" key=");
	    r.append(q[i].sortKeyInterval());
	    if (i == curr) {
		r.append(" <-");
	    }
	    r.append("\n");
	}

	r.append("new----------------------------\n");
	for (int i=idx_new + 1; i < q.length; ++i) {
	    if (i == limit_new) {
		r.append("--new limit--\n");
	    }

	    r.append(i);
	    r.append(" serial=");
	    r.append(q[i].serial);
	    r.append(" re0=");
	    r.append(q[i].rememorise0());
	    r.append(" re1=");
	    r.append(q[i].rememorise1());
	    r.append(" sn0=");
	    r.append(q[i].seenButNotMemorised0());
	    r.append(" sn1=");
	    r.append(q[i].seenButNotMemorised1());
	    if (i == curr) {
		r.append(" <-");
	    }
	    r.append("\n");
	}

	r.append("-------------------------------\n");
	r.append("nstats=");
	r.append(q.length);
	r.append(", ");
	r.append("days_since_start=");
	r.append(days_since_start);
	r.append(", ");
	r.append("num_scheduled=");
	r.append(num_scheduled);
	r.append("\n");
	r.append("idx_new=");
	r.append(idx_new);
	r.append(", ");
	r.append("limit_new=");
	r.append(limit_new);
	r.append(", ");
	r.append("curr=");
	r.append(curr);
	r.append(", ");
	r.append("first=");
	r.append(first);
	r.append("\n");

	return r.toString();
    }

}

