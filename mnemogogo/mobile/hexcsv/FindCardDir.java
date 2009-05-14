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
import java.util.Enumeration;
import java.util.Vector;
import javax.microedition.io.Connector;
import javax.microedition.io.file.FileConnection;
import javax.microedition.io.file.FileSystemRegistry;

public class FindCardDir
{
    public static String[] standard = { "cards/" };

    public static boolean isCardDir(FileConnection fconn)
    {
	boolean hasStats = false;
	boolean hasCategories = false;
	boolean hasConfig = false;
	boolean hasLastDay = false;
	boolean hasStartTime = false;
	boolean hasCards = false;

	try {

	    if (!fconn.exists() || !fconn.isDirectory() ||
		!(fconn.canRead() && fconn.canWrite()))
	    {
		return false;
	    }

	    Enumeration e = fconn.list();
	    while (e.hasMoreElements()) {
		String f = (String)e.nextElement();

		if (f.equals("stats.csv")) {
		    hasStats = true;

		} else if (f.equals("categories")) {
		    hasCategories = true;

		} else if (f.equals("config")) {
		    hasConfig = true;

		} else if (f.equals("last_day")) {
		    hasLastDay = true;

		} else if (f.equals("start_time")) {
		    hasStartTime = true;

		} else if (f.equals("cards/")) {
		    hasCards = true;

		} else if (f.equals("cards.db")) {
		    hasCards = true;
		}
	    }

	} catch (IOException e) {
	    return false;
	} catch (SecurityException e) {
	    return false;
	}

	return (hasStats
		&& hasCategories
		&& hasConfig
		&& hasLastDay
		&& hasStartTime
		&& hasCards);
    }

    public static boolean isCardDir(StringBuffer path) {
	boolean r = false;

	try {
	    FileConnection fconn =
		(FileConnection)Connector.open(path.toString(),
					       Connector.READ);
	    r = isCardDir(fconn);
	    fconn.close();
	} catch (IOException e) {
	} catch (SecurityException e) {
	}

	return r;
    }

    private static void doDir(FileConnection fconn,
			      StringBuffer pathbuf, Vector found)
    {
	try {
	    if (isCardDir(fconn)) {
		found.addElement(pathbuf.toString());
		fconn.close();

	    } else {
		Enumeration e = fconn.list();
		fconn.close();
		fconn = null;
		int orig_len = pathbuf.length();

		while (e.hasMoreElements()) {
		    pathbuf.delete(orig_len, pathbuf.length());
		    pathbuf.append((String)e.nextElement());

		    FileConnection c =
			(FileConnection)Connector.open(pathbuf.toString(),
						       Connector.READ);
		    if (c.isDirectory() && c.canRead()) {
			doDir(c, pathbuf, found);
		    }
		}
	    }
	} catch (IOException e) {
	} catch (SecurityException e) {
	}

	return;
    }


    public static String[] list() {
	Vector paths = new Vector();
	StringBuffer pathbuf = new StringBuffer("file://");

	Enumeration roots = FileSystemRegistry.listRoots();
	while (roots.hasMoreElements()) {
	    try {
		pathbuf.delete(7, pathbuf.length());
		pathbuf.append("/");
		pathbuf.append((String)roots.nextElement());

		FileConnection root =
		    (FileConnection)Connector.open(pathbuf.toString(),
						   Connector.READ);
		doDir(root, pathbuf, paths);
		root.close();
	    } catch (IOException e) {
	    } catch (SecurityException e) {
	    }
	}

	if (paths.isEmpty()) {
	    return null;
	}

	String r[] = new String[paths.size()];
	paths.copyInto(r);

	return r;
    }

    public static String[] checkStandard() {
	Vector paths = new Vector();
	StringBuffer pathbuf = new StringBuffer("file://");

	Enumeration roots = FileSystemRegistry.listRoots();
	while (roots.hasMoreElements()) {
	    try {
		pathbuf.delete(7, pathbuf.length());
		pathbuf.append("/");
		pathbuf.append((String)roots.nextElement());

		for (int i = 0; i < standard.length; ++i) {
		    int last = pathbuf.length();
		    pathbuf.append(standard[i]);

		    if (isCardDir(pathbuf)) {
			paths.addElement(pathbuf.toString());
		    }

		    pathbuf.delete(last, pathbuf.length());
		}

	    } catch (SecurityException e) { }
	}

	if (paths.isEmpty()) {
	    return null;
	}

	String r[] = new String[paths.size()];
	paths.copyInto(r);

	return r;
    }
}

