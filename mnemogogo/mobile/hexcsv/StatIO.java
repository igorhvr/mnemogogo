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
import java.io.IOException;
import java.io.EOFException;

class StatIO
{
    static String readLine(InputStreamReader in)
	throws IOException
    {
	StringBuffer s = new StringBuffer(20);
	
	try {
	    int b = in.read();
	    while (b != -1 && b != '\n') {
		s.append((char)b);
		b = in.read();
	    }
	} catch (EOFException e) { }

	return s.toString();
    }

    static String read(InputStreamReader in)
	throws IOException
    {
	StringBuffer s = new StringBuffer(20);
	int b = in.read();
	
	while (b != -1 && b != ',' && b != '\n') {
	    s.append((char)b);
	    b = in.read();
	}

	return s.toString();
    }

    static int readHexInt(InputStreamReader in)
	throws IOException
    {
	return Integer.parseInt(read(in), 16);
    }

    static long readHexLong(InputStreamReader in)
	throws IOException
    {
	return Long.parseLong(read(in), 16);
    }

    static int readInt(InputStreamReader in)
	throws IOException
    {
	return Integer.parseInt(read(in));
    }

    static long readLong(InputStreamReader in)
	throws IOException
    {
	return Long.parseLong(read(in));
    }

    private static void write(OutputStreamWriter out, int len, String str)
	throws IOException
    {
	for (int i=str.length(); i < len; ++i) {
	    out.write('0');
	}

	out.write(str, 0, str.length());
    }

    static void writeString(OutputStreamWriter out, String str)
	throws IOException
    {
	write(out, 0, str);
    }

    static void writeBool(OutputStreamWriter out, boolean d, String sep)
	throws IOException
    {
	write(out, 1, (d?"1":"0"));
	write(out, 0, sep);
    }

    static void writeBool(OutputStreamWriter out, boolean d)
	throws IOException
    {
	write(out, 1, (d?"1":"0"));
    }

    static void writeHexLong(OutputStreamWriter out, long d, String sep)
	throws IOException
    {
	write(out, 8, Long.toString(d, 16));
	write(out, 0, sep);
    }

    static void writeHexLong(OutputStreamWriter out, long d)
	throws IOException
    {
	write(out, 8, Long.toString(d, 16));
    }

    static void writeLong(OutputStreamWriter out, long d, String sep)
	throws IOException
    {
	write(out, 8, Long.toString(d));
	write(out, 0, sep);
    }

    static void writeLong(OutputStreamWriter out, long d)
	throws IOException
    {
	write(out, 8, Long.toString(d));
    }

    static void writeHexInt(OutputStreamWriter out, int d, String sep)
	throws IOException
    {
	write(out, 4, Integer.toHexString(d));
	write(out, 0, sep);
    }

    static void writeHexInt(OutputStreamWriter out, int d)
	throws IOException
    {
	write(out, 4, Integer.toHexString(d));
    }

    static void writeInt(OutputStreamWriter out, int d, String sep)
	throws IOException
    {
	write(out, 4, Integer.toString(d));
	write(out, 0, sep);
    }

    static void writeInt(OutputStreamWriter out, int d)
	throws IOException
    {
	write(out, 4, Integer.toString(d));
    }

    static void writeFloat(OutputStreamWriter out, float f, String sep)
	throws IOException
    {
	write(out, 0, Float.toString(f));
	write(out, 0, sep);
    }

    static void writeFloat(OutputStreamWriter out, float f)
	throws IOException
    {
	write(out, 0, Float.toString(f));
    }
}

