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
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.io.EOFException;
import javax.microedition.io.Connector;
import javax.microedition.io.file.FileConnection;

public class Unpack
{
    static int bufferLen = 1024;
    byte[] buffer = new byte[bufferLen];
    int pos;
    Progress progress;

    public Unpack(Progress p)
    {
	progress = p;
    }

    boolean readByte(DataInputStream src)
	throws IOException
    {
	int b = src.read();

	if (b == -1) {
	    return false;
	} else {
	    // assumes buffer is big enough
	    buffer[pos++] = (byte)b;
	}

	return true;
    }

    String readFilename(DataInputStream src)
	throws IOException, EOFException
    {
	pos = 0;
	while (readByte(src) && buffer[pos - 1] != '\n') {}

	if (pos == 0) {
	    throw new EOFException();
	}

	progress.updateOperation(pos);
	return new String(buffer, 0, pos - 1, "UTF-8");
    }

    int readDecimal(DataInputStream src)
	throws IOException
    {
	int value = 0;
	int len = 0;
	pos = 0;
	while (readByte(src) && (char)buffer[0] != '\n') {
	    pos = 0;
	    value = (value * 10) + Character.digit((char)buffer[0], 10);
	    ++len;
	}

	progress.updateOperation(len);
	return value;
    }

    void copyBytes(DataInputStream in, DataOutputStream out, int len)
	throws IOException
    {
	int s = 0;

	while (len > 0 && s >= 0)  {
	    s = in.read(buffer, 0, Math.min(len, bufferLen));
	    if (s >= 0) {
		out.write(buffer, 0, s);
		len -= s;
	    }
	}
    }

    void unpackFile(StringBuffer path, DataInputStream src)
	throws IOException
    {
	int origPathLen = path.length();
	String filename = readFilename(src);

	path.append(filename);
	int size = readDecimal(src);

	FileConnection c = (FileConnection)Connector.open(path.toString(),
	    Connector.READ_WRITE);
	c.create();
	DataOutputStream dst = c.openDataOutputStream();
	copyBytes(src, dst, size);

	// Strip of the trailing new line
	pos = 0;
	readByte(src);

	progress.updateOperation(size + 1);
	path.delete(origPathLen, path.length());
	dst.close();
	c.close();
    }

    public void unpack(DataInputStream src, String destpath)
	throws IOException
    {
	StringBuffer dstpath = new StringBuffer(destpath);

	try {
	    while (true) {
		unpackFile(dstpath, src);
	    }
	} catch (EOFException e) { }

	src.close();
    }

    public void unpack(String filepath, String destpath)
	throws IOException
    {
	DataInputStream is = Connector.openDataInputStream(filepath.toString());
	unpack(is, destpath);
    }
}

