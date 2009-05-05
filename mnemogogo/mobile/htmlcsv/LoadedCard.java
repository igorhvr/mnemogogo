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

package mnemogogo.mobile.htmlcsv;

import java.lang.*;
import java.io.IOException;
import java.io.InputStreamReader;
import javax.microedition.io.Connector;

public class LoadedCard
{
    private StringBuffer cardPath;
    private int cardPathLen;
    private int bufLen = 255;
    private char[] buf = new char[bufLen];

    public Card card;
    public boolean isOverlay = false;
    public StringBuffer question = new StringBuffer(2000);
    public StringBuffer answer = new StringBuffer(2000);

    public LoadedCard(String path) {
	cardPath = new StringBuffer(path);
	cardPath.append("cards/");
	cardPathLen = cardPath.length();
    }

    private void makeQuestionPath() {
	int a = card.serial / 10;
	int i = 0;

	cardPath.delete(cardPathLen, cardPath.length());

	while (a > 0) {
	    i += 1;
	    a = a / 10;
	}
	i = 3 - i;

	cardPath.append("Q");
	while (i > 0) {
	    cardPath.append("0");
	    --i;
	}
	cardPath.append(card.serial);
	cardPath.append(".txt");
    }

    private void makeAnswerPath() {
	cardPath.setCharAt(cardPathLen, 'A');
    }

    private void readStyleLine(InputStreamReader in)
	throws IOException
    {
	String style = StatIO.readLine(in);
	isOverlay = (style.indexOf("answerbox: overlay") != -1);
    }

    private void load(boolean isQuestion)
	throws IOException
    {
	StringBuffer data;
	int read;
	InputStreamReader in = new InputStreamReader(
	    Connector.openInputStream(cardPath.toString()), HtmlCsv.utf8);

	if (isQuestion) {
	    readStyleLine(in);
	    data = question;
	} else {
	    data = answer;
	}

	data.delete(0, data.length());
	read = in.read(buf, 0, bufLen);
	while (read != -1) {
	    data.append(buf, 0, read);
	    read = in.read(buf, 0, bufLen);
	}

	in.close();
    }

    public void loadCard(Card c)
	throws IOException
    {
	card = c;
	makeQuestionPath();
	load(true);
	makeAnswerPath();
	load(false);
    }

}

