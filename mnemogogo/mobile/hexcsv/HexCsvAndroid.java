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

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.DataInputStream;
import java.io.OutputStream;
import java.io.InputStream;
import java.io.IOException;
import java.io.FileNotFoundException;
import android.content.Context;

public class HexCsvAndroid
    extends HexCsv
{
    public static final String demo_prefix = "/android_asset/";
    public static Context context = null;

    public HexCsvAndroid(String path, Progress prog)
        throws Exception, IOException
    {
        super(path, prog, false);
    }

    protected OutputStream openAppend(String path)
        throws IOException
    {
        return new FileOutputStream(path, true);
    }
    
    protected String getStatsName(String original)
    {
        return original.replace(File.separatorChar, '-');
    }

    protected InputStream openIn(String path)
        throws IOException
    {
        if ((context != null) && path.startsWith(demo_prefix)) {
            String subpath = path.substring(demo_prefix.length());

            if (subpath.endsWith("STATS.CSV")) {
                try {
                    return context.openFileInput(getStatsName(subpath));
                } catch (FileNotFoundException e) {}
            }

            return context.getAssets().open(subpath);
        }

        return new FileInputStream(path);
    }

    protected OutputStream openOut(String path)
        throws IOException
    {
        if ((context != null) && path.startsWith(demo_prefix))
        {
            String subpath = path.substring(demo_prefix.length());
            return context.openFileOutput(getStatsName(subpath), Context.MODE_PRIVATE);
        }

        return new FileOutputStream(new File(path));
    }

    protected DataInputStream openDataIn(String path)
        throws IOException
    {
        return new DataInputStream(openIn(path));
    }
}

