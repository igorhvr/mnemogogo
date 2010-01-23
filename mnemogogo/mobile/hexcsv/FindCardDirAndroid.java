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

import java.io.IOException;
import java.util.Enumeration;
import java.util.Vector;
import java.io.File;

public class FindCardDirAndroid
{
    public static String[] standard = { "cards/" };

    public static boolean isCardDir(File file)
    {
        boolean hasStats = false;
        boolean hasCategories = false;
        boolean hasConfig = false;
        boolean hasCards = false;

        try {

            if (!file.exists() || !file.isDirectory() || !file.canRead())
            {
                return false;
            }

            String[] subfiles = file.list();
            for (String sf : subfiles) {

                if (sf.equals("STATS.CSV")) {
                    hasStats = true;

                } else if (sf.equals("CATS")) {
                    hasCategories = true;

                } else if (sf.equals("CONFIG")) {
                    hasConfig = true;

                } else if (sf.equals("CARDS")) {
                    hasCards = true;
                }
            }

        } catch (SecurityException e) {
            return false;
        }

        return (file.canWrite()
                && hasStats
                && hasCategories
                && hasConfig
                && hasCards);
    }

    private static void doDir(File dir, Vector<String> found)
    {
        try {
            if (isCardDir(dir)) {
                found.addElement(dir.getPath());

            } else {
                String[] subfiles = dir.list();
                for (String sf : subfiles) {
                    File subdir = new File(dir, sf);

                    if (subdir.isDirectory() && subdir.canRead()) {
                        doDir(subdir, found);
                    }
                }
            }
        } catch (SecurityException e) {
        }

        return;
    }


    public static String[] list() {
        Vector<String> paths = new Vector<String>();

        try {
            File[] roots = File.listRoots();
            for (File root : roots) {
                doDir(root, paths);
            }
        } catch (SecurityException e) {
            return null;
        }

        if (paths.isEmpty()) {
            return null;
        }

        String r[] = new String[paths.size()];
        paths.copyInto(r);

        return r;
    }

}

