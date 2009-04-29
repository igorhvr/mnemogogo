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

import java.io.*;
import java.util.Hashtable;
import java.util.Enumeration;

public class Config extends Hashtable<String, String>
{
    Config() {
	put("grade_0_items_at_once", "10");
	put("sorting", "1");
	put("logging", "1");
	put("day_starts_at", "3");
    }

    Config(InputStreamReader in)
	throws IOException
    {
	readConfig(in);
    }

    public int grade0ItemsAtOnce() {
	return Integer.parseInt(get("grade_0_items_at_once"));
    }

    public int dayStartsAt() {
	return Integer.parseInt(get("day_starts_at"));
    }

    public boolean logging() {
	return (get("logging") != "0");
    }

    public boolean sorting() {
	return (get("sorting") != "0");
    }

    public void writeConfig(DataOutput out)
	throws IOException
    {
	for (Enumeration<String> e = elements(); e.hasMoreElements(); ) {
	    String key = e.nextElement(); 
	    StringBuffer line = new StringBuffer();

	    line.append(key);
	    line.append("=");
	    line.append(get(key));
	    line.append("\n");

	    try {
		out.write(line.toString().getBytes("ASCII"));
	    } catch (UnsupportedEncodingException x) {
		throw new IOException("Unsupported encoding: ASCII");
	    }
	}
    }

    private void readConfig(InputStreamReader in)
	throws IOException
    {
	StringBuffer namebuf = new StringBuffer(30);
	StringBuffer valuebuf = new StringBuffer(10);
	StringBuffer curr = namebuf;
	int c;

	try { while (true) {
	    namebuf.delete(0, namebuf.length());
	    valuebuf.delete(0, valuebuf.length());
	    curr = namebuf;

	    c = in.read();
	    while (c != '\n') {
		if (c == '=') {
		    curr = valuebuf;
		} else {
		    curr.append((char)c);
		}
	    }

	    if (curr != valuebuf) {
		throw new EOFException();
	    }

	    String name = namebuf.toString();
	    String value = valuebuf.toString();
	    put(name, value);

	} } catch (EOFException e) {}
    }
}

