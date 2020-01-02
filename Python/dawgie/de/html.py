'''
COPYRIGHT:
Copyright (c) 2015-2020, California Institute of Technology ("Caltech").
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
import html
import io

import dawgie


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

    def add_table (self, clabels:[str], rows:int=0, title:str=None)->'dawgie.TableVisitor':
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
    void_elements = ["area", "base", "br", "col", "embed", "hr", "img",
                     "input", "link", "meta", "param", "source", "track",
                     "wbr"]

    def __init__(self):
        Cell.__init__(self)
        self.__css = []
        self.__decl = []
        self.__js = []
        self.__stylesheet = []
        self.__title = 'Undefined Visitee'
        pass

    def add_declaration(self, text: str, **kwds) -> None:
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

    def add_declaration_inline(self, text: str, **kwds) -> None:
        # attributes that apply to presentation
        # class allows application of predefined css within preloaded
        #     stylesheets files -- if file isn't preloaded there is no effect
        claz = (' class="' + kwds['class'] + '" ') if 'class' in kwds else ''
        # id allows reference via scripting and link references
        idd = (' id="' + kwds['id'] + '" ') if 'id' in kwds else ''
        # style allows direct application of raw css to enclosed content
        style = (' style="' + kwds['style'] + '" ') if 'style' in kwds else ''

        # tags for configuration settings (e.g. __<custom_name> in class vars)
        # plain text representing a raw stylesheet that will be embedded directly
        #     into the document via a style tag
        if 'css' in kwds:
            self.__css.append(kwds['css'])
        # fully qualified (entire) tags for js -- maintain for backwards comp
        if 'js' in kwds:
            self.__js.append(kwds['js'])
        # list of relative uris from SV display page directory,
        #     e.g. '../../stylesheets/application.css'
        if 'stylesheet' in kwds:
            self.__stylesheet.append(str(kwds['stylesheet']))
        # title composed from text, value ignored -- maintain for backwards comp
        if 'title' in kwds:
            # if defined use title value and ignore text
            if kwds['title'] is not None and len(str(kwds['title']).strip()) > 0:
                self.__title = html.escape(str(kwds['title']))
            else:
                self.__title = html.escape(text)

        # content + tags for presentation (e.g. __decl in class vars)
        # fully qualified (entire) tags for div -- maintain for backwards comp
        #     note: closing tag must subsequently be specified, also
        if 'div' in kwds:
            self.__content.append(kwds['div'])
        # text content is escaped and embedded in paragraph tag by default
        #     unless different tag is specified in kwds
        if text and 'title' not in kwds:
            tag = str(kwds['tag']) if 'tag' in kwds else 'p'
            tag = tag if len(tag.strip()) > 0 else 'p'
            tag_open = '<' + tag + idd + claz + style + '>'
            tag_close = ('</' + tag + '>') if tag not in self.void_elements else ''
            self.__content.append(tag_open + html.escape(text) + tag_close)
        # NOTE that list and pre are placed below text to allow a compound
        #     add_declaration statement that includes text, tag, pre and/or
        #     list that places a paragraph above the formatted content to
        #     allow prose to describe the reported values
        # lists -- list should actually be a list of items as a str will parse
        #          into its constituent chars
        if 'list' in kwds:
            # value of enum is ignored but presence implies numbered list
            tag_for_list = 'ol' if 'enum' in kwds else 'ul'
            self.__content.append('<' + tag_for_list + idd + claz + style + '>')
            for item in list(kwds['list']):
                self.__content.append('<li>' + html.escape(item) + '</li>')
            self.__content.append('</' + tag_for_list + '>')
        # pre -- display preformatted text
        if 'pre' in kwds:
            tag_open = '<pre' + idd + claz + style + '>'
            tag_close = '</pre>'
            self.__content.append(tag_open + str(kwds['pre']) + tag_close)
        return

    def render(self) -> str:
        buf = io.StringIO()
        buf.write(f"<!DOCTYPE HTML>")
        buf.write(f"<html lang=\"en-US\">")
        buf.write(f"    <head>")
        buf.write(f"        <meta charset=\"UTF-8\">")
        buf.write(f"        <title>{self.__title}</title>")
        buf.write(f"        <script " +
                  "src=\"https://cdn.pydata.org/bokeh/release/bokeh-{bokeh.__version__}.min.js\"></script>")
        buf.write(f"        <script " +
                  "src=\"https://cdn.pydata.org/bokeh/release/bokeh-widgets-{bokeh.__version__}.min.js\"></script>")
        buf.write(f"        <script " +
                  "src=\"https://cdn.pydata.org/bokeh/release/bokeh-tables-{bokeh.__version__}.min.js\"></script>")
        for js in self.__js:
            buf.write("        " + js)
        for stylesheet in self.__stylesheet:
            # <link rel = "stylesheet" type = "text/css" href = "myStyle.css" />
            # <link href="mystyles.css" rel="preload" as="style">
            tag_for_stylesheet = "        <link href=\"" + stylesheet + "\" rel=\"preload\" as=\"style\">"
            buf.write(tag_for_stylesheet)
        for css in self.__css:
            tag_for_css = "        <style>" + css + "</style>"
            buf.write(tag_for_css)
        buf.write(f"    </head>")
        buf.write(f"    <body>")
        # 20200102: next op for backwards compatibility
        for d in self.__decl:
            buf.write(d)
        # iff using add_declaration_inline(...) then declarations are
        #     rendered in order with add_primitive(...), tables, etc.
        self._render(buf)
        buf.write(f"    </body>")
        buf.write(f"</html>")
        return buf.getvalue()

    pass
