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
import java.io.IOException;
import java.io.PrintStream;
import java.util.Enumeration;
import javax.microedition.io.Connector;
import javax.microedition.io.file.FileSystemRegistry;

public class Debug
{
    public static PrintStream logFile = null;

    public Debug() {
	StringBuffer path = new StringBuffer("file://");
	Enumeration roots = FileSystemRegistry.listRoots();

	while (roots.hasMoreElements()) {
	    try {
		path.delete(7, path.length());
		path.append("/");
		path.append((String)roots.nextElement());
		path.append("mnemogogo.log");

		logFile = new PrintStream(
		    Connector.openOutputStream(path.toString()));

		if (logFile != null) {
		    break;
		}
	    } catch (SecurityException e) {
	    } catch (IOException e) {}
	}
    }

    public static void log(String msg) {
	logFile.print(msg);
	logFile.flush();
    }

    public static void log(int msg) {
	logFile.print(msg);
	logFile.flush();
    }

    public static void log(long msg) {
	logFile.print(msg);
	logFile.flush();
    }

    public static void stopLog() {
	if (logFile != null) {
	    logFile.close();
	    logFile = null;
	}
    }
}

