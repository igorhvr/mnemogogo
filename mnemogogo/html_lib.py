#
# By Fredrik Lundh, October 28, 2006
# http://effbot.org/zone/re-sub.htm#unescape-html
#

import re
try:
    from html.entities import name2codepoint # >= Python 3.0
    htmltounicode_working = True
except:
    try:
        from htmlentitydefs import name2codepoint # <  Python 3.0
        htmltounicode_working = True
    except:
        htmltounicode_working = False

##
# Removes HTML or XML character references and entities from a text string.
#
# @param text The HTML (or XML) source text.
# @return The plain text, as a Unicode string, if necessary.

if htmltounicode_working:
    def htmltounicode(text):
        def fixup(m):
            text = m.group(0)
            if text[:2] == "&#": # character reference
                try:
                    if text[:3] == "&#x":
                        return unichr(int(text[3:-1], 16))
                    else:
                        return unichr(int(text[2:-1]))
                except ValueError:
                    pass
            elif text[1:-1] not in ["lt", "amp", "gt", "quot", "apos"]: # named entity
                try:
                    text = unichr(name2codepoint[text[1:-1]])
                except KeyError:
                    pass
            return text # leave as is

        return re.sub("&#?\w+;", fixup, text)

else:
    def htmltounicode(text):
        return text

