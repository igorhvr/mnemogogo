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

import java.util.Vector;
import java.io.File;
import java.io.IOException;

public class FindCardDirAndroid
{
    public static String[] standard = { "cards/" };
    
    private static final String[] skip_files = { "LOST.DIR", ".thumbnails" };
    private static final String[] skip_paths = { "/etc", "/system",
        "/sys", "/cache", "/sbin", "/proc", "/d", "/dev" };

    private static boolean hasAllFiles(String[] subfiles)
    {
        boolean hasStats = false;
        boolean hasCategories = false;
        boolean hasConfig = false;
        boolean hasCards = false;

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

        return (   hasStats
                && hasCategories
                && hasConfig
                && hasCards);
    }

    public static boolean isCardDir(File file)
    {
        String[] subfiles;

        try {

            if (!file.exists() || !file.isDirectory() || !file.canRead())
            {
                return false;
            }

            subfiles = file.list();

        } catch (SecurityException e) {
            return false;
        }

        return (file.canWrite() && hasAllFiles(subfiles));
    }

    public static boolean isCardDir(String path)
    {
        if ((HexCsvAndroid.context != null)
            && path.startsWith(HexCsvAndroid.demo_prefix))
        {
            String subpath = path.substring(HexCsvAndroid.demo_prefix.length());
            
            if (subpath.endsWith(File.separator)) {
                subpath = subpath.substring(0, subpath.length() - 1);
            }
            
            try {
                return hasAllFiles(
                        HexCsvAndroid.context.getAssets().list(subpath));
            } catch (IOException e) {
                return false;
            }
        }

        return isCardDir(new File(path));
    }

    private static boolean skipFile(File f)
    {
        String name = f.getName();
        for (String g : skip_files) {
                if (name.equals(g)) {
                        return true;
                }
        }
        
        String path = f.getAbsolutePath();
        for (String g : skip_paths) {
                if (path.equals(g)) {
                        return true;
                }
        }
        
        return false;
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

                    if (subdir.isDirectory() && subdir.canRead() && !skipFile(subdir)) {
                        doDir(subdir, found);
                    }
                }
            }
        } catch (SecurityException e) {
        }

        return;
    }


    public static Vector<String> list(boolean check_filesystem) {
        Vector<String> paths = new Vector<String>();

        try {
            if (check_filesystem) {
                // Check on the filesystem
                File[] roots = File.listRoots();
                for (File root : roots) {
                    String s = root.toString();
                    int bidx = s.indexOf(0);
                    if (bidx != -1) {
                            // work around an Android bug
                            // http://www.mail-archive.com/android-developers@googlegroups.com/msg42592.html
                            s = s.substring(0, bidx);
                    }
                    doDir(new File(s), paths);
                }
            }

            // Check in assets
            if (HexCsvAndroid.context != null) {
                try {
                    for (String demo : HexCsvAndroid.context.getAssets().list(""))
                    {
                        String path = new File("/android_asset", demo).getPath();
                        if (isCardDir(path)) {
                            paths.addElement(path);
                        }
                    }
                } catch (IOException e) { }
            }
        } catch (SecurityException e) {
            return null;
        }

        return paths;
    }

}

