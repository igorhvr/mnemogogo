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

import java.io.DataInputStream;
import java.io.IOException;
import java.io.EOFException;

class CardData
{
    static int bufferLen = 10;
    byte[] buffer = new byte[bufferLen];
    int pos;
    Progress progress;

    public CardData(DataInputStream is, Progress p, CardDataSet carddb)
        throws IOException
    {
        progress = p;
        load(is, carddb);
        bufferLen = 10;
        buffer = new byte[bufferLen];
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

        return value;
    }

    String readString(DataInputStream src)
        throws IOException
    {
        int len = readDecimal(src);

        if (bufferLen < len) {
            bufferLen = len;
            buffer = new byte[bufferLen];
        }

        pos = 0;
        while (readByte(src) && pos < len) {}

        if (pos == 0) {
            throw new EOFException();
        }

        String r = new String(buffer, 0, pos, "UTF-8");

        // Strip of the trailing new line
        pos = 0;
        readByte(src);

        return r;
    }

    void skipString(DataInputStream src)
        throws IOException
    {
        int len = readDecimal(src) + 1; // + \n

        while (len > 0) {
            len -= src.skip(len);
        }
    }

    private void load(DataInputStream src, CardDataSet carddb)
        throws IOException
    {
        int num_cards = readDecimal(src);
        int overlay;
        String qcard = null;
        String acard = null;

        try {
            for (int i = 0; i < num_cards; ++i) {
                overlay = readDecimal(src);
                if (carddb.cardDataNeeded(i)) {
                    qcard = readString(src);
                    acard = readString(src);
                    carddb.setCardData(i, qcard, acard, overlay != 0);
                } else {
                    skipString(src);
                    skipString(src);
                }
                if (i % 10 == 0) {
                    progress.updateOperation(10);
                }
            }
        } catch (EOFException e) { }

        src.close();
    }
}

