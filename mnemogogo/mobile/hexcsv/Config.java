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
import java.io.IOException;
import java.io.EOFException;
import java.util.Hashtable;
import java.util.Enumeration;

public class Config extends Hashtable/*<String, String>*/
{
    Config() {
	setDefaults();
    }

    Config(InputStreamReader in)
	throws IOException
    {
	setDefaults();
	readConfig(in);
    }

    private void setDefaults() {
	put("grade_0_items_at_once", "10");
	put("sorting", "1");
	put("logging", "1");
	put("day_starts_at", "3");
    }

    public int grade0ItemsAtOnce() {
	return Integer.parseInt((String)get("grade_0_items_at_once"));
    }

    public int dayStartsAt() {
	return Integer.parseInt((String)get("day_starts_at"));
    }

    public String getString(String key) {
	return (String)get(key);
    }

    public boolean logging() {
	String s = (String)get("logging");
	return (!s.equals("0"));
    }

    public boolean sorting() {
	String s = (String)get("sorting");
	return (!s.equals("0"));
    }

    public void writeConfig(OutputStreamWriter out)
	throws IOException
    {
	StringBuffer line = new StringBuffer(100);

	Enumeration/*<String>*/ e = elements();
	while (e.hasMoreElements()) {
	    String key = (String)e.nextElement(); 
	    line.delete(0, line.length());

	    line.append(key);
	    line.append("=");
	    line.append(get(key));
	    line.append("\n");

	    out.write(line.toString(), 0, line.length());
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
	    while (c != -1 && c != '\n') {
		if (c == '=') {
		    curr = valuebuf;
		} else {
		    curr.append((char)c);
		}
		c = in.read();
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

