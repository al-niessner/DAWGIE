'''
COPYRIGHT:
Copyright (c) 2015-2019, California Institute of Technology ("Caltech").
U.S. Government sponsorship acknowledged.

All rights reserved.

LICENSE:
Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

- Redistributions of source code must retain the above copyright notice,
this list of conditions and the following disclaimer.

- Redistributions in binary form must reproduce the above copyright
notice, this list of conditions and the following disclaimer in the
documentation and/or other materials provided with the distribution.

- Neither the name of Caltech nor its operating division, the Jet
Propulsion Laboratory, nor the names of its contributors may be used to
endorse or promote products derived from this software without specific prior
written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.

NTR:
'''

import base64
import bokeh
import dawgie
import html
import io

class AsIsText(object):
    # pylint: disable=too-few-public-methods
    def __init__ (self, text):
        object.__init__ (self)
        self.__text = text
        return

    def _render (self, buf:io.StringIO): buf.write (self.__text)
    pass

class Cell(dawgie.Visitor):
    # pylint: disable=protected-access
    def __init__ (self):
        dawgie.Visitor.__init__(self)
        self.__content = []
        return

    def _render (self, buf:io.StringIO)->None:
        for c in self.__content: c._render (buf)
        return

    def add_declaration (self, text:str, **kwds)->None:
        raise NotImplementedError()

    def add_image (self, alternate:str, label:str, img:bytes)->None:
        content = ('<h3>' + label + '</h3>') if label else ''
        content += '<img alt="' + html.escape (alternate) + '" src="data:image/png;base64,'
        content += base64.encodebytes (img).decode()
        content += '">'
        self.__content.append (AsIsText(content))
        return

    def add_primitive (self, value, label:str=None)->None:
        content = (label + ' = ') if label else ''
        content += str (value)
        self.__content.append (AsIsText('<p>' + html.escape (content) + '</p>'))
        return

    def add_table (self, clabels:[str], rows:int=0, title:str=None)->'TableVisitor':
        self.__content.append (Table(clabels, rows, title))
        return self.__content[-1]
    pass

class Table(dawgie.TableVisitor):
    # pylint: disable=protected-access,too-few-public-methods
    def __init__ (self, clabels:[str], rows=0, title=None)->None:
        dawgie.TableVisitor.__init__ (self)
        self.__clabels = clabels
        self.__table = [[Cell() for c in range (len (clabels))]
                        for r in range (rows)]
        self.__title = title
        return

    def _render (self, buf:io.StringIO)->None:
        if not self.__table: return

        buf.write ('<table style="border: 5px solid black; border-collapse: collapse">')

        if self.__title: buf.write ('<caption style="text-align:left">' +
                                    self.__title + '</caption>')
        if len (self.__clabels) < len (self.__table[0]):
            self.__clabels.extend (['??' for c in range (len (self.__table[0]) -
                                                         len (self.__clabels))])
            pass

        buf.write ('<tr>')
        for h in self.__clabels[:len (self.__table[0])]:
            buf.write ('<th style="border: 2px solid black; border-collapse: collapse; padding: 5px;">')
            buf.write (html.escape (h))
            buf.write ('</th>')
            pass
        buf.write ('</tr>')
        for r in self.__table:
            buf.write ('<tr>')
            for c in r:
                buf.write('<td align="center" style="border: 2px solid black; border-collapse: collapse; padding: 5px;">')
                c._render (buf)
                buf.write ('</td>')
                pass
            buf.write ('</tr>')
        buf.write ('</table>')
        return

    def get_cell (self, r:int, c:int)->dawgie.Visitor:
        if len (self.__table) <= r:
            self.__table.extend ([[Cell() for c in range (len (self.__clabels))] for i in
                                  range (r - len (self.__table) + 1)])

        col = self.__table[r]

        if len (col) <= c:
            for cc in self.__table: cc.extend ([Cell() for c in
                                                range (c - len (col) + 1)])
            pass
        return self.__table[r][c]
    pass

class Visitor(Cell):
    def __init__ (self):
        Cell.__init__ (self)
        self.__decl = []
        self.__js = []
        self.__title = 'Undefined Visitee'
        pass

    def add_declaration (self, text:str, **kwds)->None:
        style = (' style="' + kwds['style'] + '" ') if 'style' in kwds else ''

        if 'div' in kwds: self.__decl.append (kwds['div'])
        if 'enum' in kwds:
            if kwds['list']: self.__decl.append ('<OL' + style + '>')
            else: self.__decl.append ('</OL>')
            pass
        if 'js' in kwds: self.__js.append (kwds['js'])
        if 'list' in kwds:
            if kwds['list']: self.__decl.append ('<UL' + style + '>')
            else: self.__decl.append ('</UL>')
            pass
        if 'title' in kwds: self.__title = html.escape (text)

        if text and 'title' not in kwds:
            text = html.escape (text)
            tag = (kwds['tag'] if 'tag' in kwds else 'p') + style
            self.__decl.append ('<' + tag + '>' + text + '</' + tag + '>')
            pass
        return

    def render(self)->str:
        buf = io.StringIO()
        buf.write ('<!DOCTYPE HTML><html lang="en-US"><head>')
        buf.write ('<meta charset="UTF-8"><title>')
        buf.write (self.__title)
        buf.write ('</title>')
        buf.write ('''<script src="https://cdn.pydata.org/bokeh/release/bokeh-{0}.min.js"></script>
<script src="https://cdn.pydata.org/bokeh/release/bokeh-widgets-{0}.min.js"></script>
<script src="https://cdn.pydata.org/bokeh/release/bokeh-tables-{0}.min.js"></script>'''.format (bokeh.__version__))
        for js in self.__js: buf.write (js)
        buf.write ('</head><body>')
        for d in self.__decl: buf.write (d)
        self._render (buf)
        buf.write ('</body></html>')
        return buf.getvalue()
    pass
