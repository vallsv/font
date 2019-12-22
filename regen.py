#!/usr/bin/env python
"""
Generator for a SVG-font using 14 segments.

Read a SVG file containing a font, and regenerate
the font content using paths from the document.
"""
import itertools
import re
import html

input_filename = "fourteen-segments.svg"
output_filename = input_filename

###################################################
# FONT DESCRIPTION
###################################################

glyphs = {
    " ": ("space", ""),
    ".": ("period", "r"),
    "'": ("quotesingle", "q"),
    "#": ("numbersign", "abcdefghijklmnopqr"),
    "0": ("zero", "abcgjnopkf"),
    "1": ("one", "fgn"),
    "2": ("two", "abgihjop"),
    "3": ("three", "abghinop"),
    "4": ("four", "chign"),
    "5": ("five", "bachinpo"),
    "6": ("six", "bacjopnih"),
    "7": ("seven", "abgn"),
    "8": ("eight", "abcghijnop"),
    "9": ("nine", "ihcabgnpo"),
    "A": (None, "abcgjnhi"),
    "B": (None, "abeghilnop"),
    "C": (None, "bacjop"),
    "D": (None, "abeglnop"),
    "E": (None, "bachijop"),
    "F": (None, "bachij"),
    "G": (None, "bacjopni"),
    "H": (None, "cjhign"),
    "I": (None, "abelop"),
    "J": (None, "oleab"),
    "K": (None, "cjhfm"),
    "L": (None, "cjop"),
    "M": (None, "jcdfgn"),
    "N": (None, "jcdmng"),
    "O": (None, "abgnpojc"),
    "P": (None, "jcabgih"),
    "Q": (None, "ngbacjopm"),
    "R": (None, "higbacjm"),
    "S": (None, "badinpo"),
    "T": (None, "leab"),
    "U": (None, "cjopng"),
    "V": (None, "dmng"),
    "W": (None, "cjkmng"),
    "X": (None, "dkmf"),
    "Y": (None, "dfl"),
    "Z": (None, "abfkop"),
    "+": (None, "ehil"),
    "-": (None, "hi"),
    "*": (None, "defklm"),
    "×": ("multiply", "dfkm"),
    "/": (None, "kf"),
    "\\": (None, "dm"),
    "=": (None, "hiop"),
    "<": ("lessthan", "fm"),
    ">": ("greaterthan", "dk"),
    "[": (None, "belp"),
    "]": (None, "aelo"),
}
"""Contains the character name and the segments to enable"""

special_characters = ".'# "
"""Cause the horizontal kerning have to be tuned"""

###################################################

hkern_template = '''\
      <hkern u1="%s" u2="%s" k="%i" />
'''

glyph_template = '''\
      <glyph glyph-name="%s"
             d="%s"
             unicode="%s" />
'''

def read_data(filename):
    with open(filename, "rt") as f:
        data = f.read()
    return data

def gen_hkern_names(characters):
    names = []
    for c in characters:
        if ord(c) < 0x30:
            c = "&#x%0X;" % ord(c)
        else:
            c = html.escape(c)
        names.append(c)
    return ",".join(names)

def gen_hkern(u1, u2, size):
    u1 = gen_hkern_names(u1)
    u2 = gen_hkern_names(u2)
    return hkern_template % (u1, u2, size)

def gen_hkerns(data, glyphs):
    font = re.search(r"<font([^>]*)>", data, re.MULTILINE)
    font = font.groups()[0]
    char_width = re.search(r"horiz-adv-x=\"([^\"]*)\"", font, re.MULTILINE)
    char_width = int(char_width.groups()[0])

    characters = "".join(glyphs.keys())
    for c in special_characters:
        characters = characters.replace(c, "")
    hkerns = ""
    hkerns += gen_hkern(characters + "'", ".", char_width)
    hkerns += gen_hkern("'", characters + " ", char_width)
    return hkerns

def invert_path(path):
    result = []
    path = path.split(" ")
    for e in path:
        if "," in e:
            x, y = e.split(",")
            y = 1024 - float(y)
            e = "%s,%f" % (x, y)
        result.append(e)
    return " ".join(result)

def extract_segment_path(data):
    pattern = r"<path ((id)=\"([^\"]*)\"|(d)=\"([^\"]*)\"|.)*>"
    result = {}
    paths = re.findall(r"<path[^>]*>", data, re.MULTILINE)
    for path in paths:
        tag = re.search(r"id=\"([^\"]*)\"", path, re.MULTILINE)
        tag = tag.groups()[0]
        d = re.search(r"d=\"([^\"]*)\"", path, re.MULTILINE)
        d = d.groups()[0]
        tag = tag.replace("segment-", "")
        result[tag] = invert_path(d)
    return result

def gen_glyph(char, name, segments, paths):
    if name is None:
        name = char
    d = []
    for s in segments:
        d.append(paths[s])
    d = " ".join(d)
    return glyph_template % (name, d, html.escape(char))

def gen_glyphs(glyphs, paths):
    result = []
    keys = sorted(glyphs.keys())
    for char in keys:
        glyph = glyphs[char]
        r = gen_glyph(char, glyph[0], glyph[1], paths)
        result.append(r)
    return "".join(result)

def replace_font(data, new_data):
    # remove old content
    data = re.sub(r"<hkern[^>]*>", "", data)
    data = re.sub(r"<glyph[^>]*>", "", data)
    data = re.sub(r"\n\s*\n", "\n", data, re.MULTILINE)
    # insert the new one
    data = data.replace("</font>", new_data + "\n</font>")
    return data


raw = read_data(input_filename)
print("%s: %d B" % (input_filename, len(raw)))
paths = extract_segment_path(raw)
result = gen_glyphs(glyphs, paths)
result += gen_hkerns(raw, glyphs)

final = replace_font(raw, result)
print("Final: %d B" % (len(final),))

with open(output_filename, "wt") as f:
    f.write(final)

