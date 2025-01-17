'''
COPYRIGHT:
Copyright (c) 2015-2025, California Institute of Technology ("Caltech").
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
import re


class AsIsText:
    '''convert text to HTML as is (no decorations)'''

    # pylint: disable=too-few-public-methods
    def __init__(self, text):
        object.__init__(self)
        self.__text = text
        return

    def _render(self, buf: io.StringIO):
        buf.write(self.__text)

    pass


class Cell(dawgie.Visitor):
    '''render content into a table cell'''

    # pylint: disable=protected-access
    def __init__(self):
        dawgie.Visitor.__init__(self)
        self._content = []
        return

    def _render(self, buf: io.StringIO) -> None:
        for c in self._content:
            c._render(buf)
        return

    def add_declaration(self, text: str, **kwds) -> None:
        raise NotImplementedError()

    def add_image(self, alternate: str, label: str, img: bytes) -> None:
        content = ('<h3>' + label + '</h3>') if label else ''
        content += (
            '<img alt="'
            + html.escape(alternate)
            + '" src="data:image/png;base64,'
        )
        content += base64.encodebytes(img).decode()
        content += '">'
        self._content.append(AsIsText(content))
        return

    def add_primitive(self, value, label: str = None) -> None:
        content = (label + ' = ') if label else ''
        content += str(value)
        self._content.append(AsIsText('<p>' + html.escape(content) + '</p>'))
        return

    def add_table(
        self, clabels: [str], rows: int = 0, title: str = None
    ) -> 'dawgie.TableVisitor':
        self._content.append(Table(clabels, rows, title))
        return self._content[-1]

    pass


class Table(dawgie.TableVisitor):
    # pylint: disable=protected-access,too-few-public-methods
    def __init__(self, clabels: [str], rows=0, title=None) -> None:
        dawgie.TableVisitor.__init__(self)
        self.__clabels = clabels
        self.__table = [
            [Cell() for c in range(len(clabels))] for r in range(rows)
        ]
        self.__title = title
        return

    def _render(self, buf: io.StringIO) -> None:
        if not self.__table:
            return

        buf.write(
            '<table style="border: 5px solid black; border-collapse: collapse">'
        )

        if self.__title:
            buf.write(
                '<caption style="text-align:left">'
                + self.__title
                + '</caption>'
            )
        if len(self.__clabels) < len(self.__table[0]):
            self.__clabels.extend(
                [
                    '??'
                    for c in range(len(self.__table[0]) - len(self.__clabels))
                ]
            )
            pass

        buf.write('<tr>')
        for h in self.__clabels[: len(self.__table[0])]:
            buf.write(
                '<th style="border: 2px solid black; border-collapse: collapse; padding: 5px;">'
            )
            buf.write(html.escape(h))
            buf.write('</th>')
            pass
        buf.write('</tr>')
        for r in self.__table:
            buf.write('<tr>')
            for c in r:
                buf.write(
                    '<td align="center" style="border: 2px solid black; border-collapse: collapse; padding: 5px;">'
                )
                c._render(buf)
                buf.write('</td>')
                pass
            buf.write('</tr>')
        buf.write('</table>')
        return

    def get_cell(self, r: int, c: int) -> dawgie.Visitor:
        if len(self.__table) <= r:
            self.__table.extend(
                [
                    [Cell() for c in range(len(self.__clabels))]
                    for i in range(r - len(self.__table) + 1)
                ]
            )

        col = self.__table[r]

        if len(col) <= c:
            for cc in self.__table:
                cc.extend([Cell() for c in range(c - len(col) + 1)])
            pass
        return self.__table[r][c]

    pass


class Visitor(Cell):
    void_elements = [
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    ]

    def __init__(self):
        Cell.__init__(self)
        self.__css = []
        self.__decl = []
        self.__js = []
        self.__title = 'Undefined Visitee'
        pass

    def add_declaration(self, text: str, **kwds) -> None:
        style = (' style="' + kwds['style'] + '" ') if 'style' in kwds else ''

        if 'div' in kwds:
            self.__decl.append(kwds['div'])
        if 'enum' in kwds:
            if kwds['list']:
                self.__decl.append('<OL' + style + '>')
            else:
                self.__decl.append('</OL>')
            pass
        if 'js' in kwds:
            self.__js.append(kwds['js'])
        if 'list' in kwds:
            if kwds['list']:
                self.__decl.append('<UL' + style + '>')
            else:
                self.__decl.append('</UL>')
            pass
        if 'title' in kwds:
            self.__title = html.escape(text)

        if text and 'title' not in kwds:
            text = html.escape(text)
            tag = (kwds['tag'] if 'tag' in kwds else 'p') + style
            self.__decl.append('<' + tag + '>' + text + '</' + tag + '>')
            pass
        return

    def add_declaration_inline(self, text: str, **kwds) -> None:
        # have to walk through a bunch of possiblities of input meaning that
        # this function is basically a horde of branches. Therefore asking
        # pylint: disable=too-many-branches
        #
        # attributes that apply to presentation
        # class allows application of predefined css within preloaded
        #     stylesheets files -- if file isn't preloaded there is no effect
        claz = (
            f" class=\"{html.escape(str(kwds['class']))}\" "
            if 'class' in kwds
            else ""
        )
        # id allows reference via scripting and link references
        idd = f" id=\"{html.escape(str(kwds['id']))}\" " if 'id' in kwds else ""
        # style allows direct application of raw css to enclosed content
        # escape double-quotes only, allow single-quotations for css
        # html.escape() rules out certain advanced constructs but they can
        # be inserted via a stylesheet
        if 'style' in kwds:
            attrib_value = html.escape(str(kwds['style']), quote=False).replace(
                "\"", "&quot;"
            )
            style = f" style=\"{attrib_value}\" "
        else:
            style = ""

        # tags for configuration settings (e.g. __<custom_name> in class vars)
        # -- embed external files before inline scripts --
        # list of relative uris from SV display page directory,
        #     e.g. '../../javascripts/application.js'
        if 'javascript' in kwds:
            tag_value = html.escape(str(kwds['javascript']))
            tag_value = f"        <script type=\"text/javascript\" src=\"{tag_value}\"></script>"
            self.__js.append(tag_value)
        # list of relative uris from SV display page directory,
        #     e.g. '../../stylesheets/application.css'
        if 'stylesheet' in kwds:
            # <link rel = "stylesheet" type = "text/css" href = "myStyle.css" />
            # <link href="mystyles.css" rel="preload" as="style">
            tag_value = html.escape(str(kwds['stylesheet']))
            tag_value = f"        <link href=\"{tag_value}\" rel=\"preload\" as=\"style\">"
            self.__css.append(tag_value)
        # -- embed inline text after external files to allow customizations --
        # plain text representing a raw stylesheet that will be embedded directly
        #     into the document via a style tag
        if 'css' in kwds:
            # clean potential closing tags / limit malicious code
            tag_value = re.sub(r"<\s*/\s*style\s*>", "", str(kwds['css']))
            tag_value = f"        <style>{tag_value}</style>"
            self.__css.append(tag_value)
        # plain text representing a raw javascript block that will be embedded
        #     directly into the document via a script tag
        if 'js' in kwds:
            # clean potential closing tags / limit malicious code
            tag_value = re.sub(r"<\s*/\s*script\s*>", "", str(kwds['js']))
            tag_value = (
                f"        <script type=\"text/javascript\">{tag_value}</script>"
            )
            self.__js.append(tag_value)
        # title composed from text, value ignored -- maintain for backwards comp
        if 'title' in kwds:
            # if defined use title value and ignore text
            if kwds['title'] is not None and str(kwds['title']).strip():
                self.__title = html.escape(str(kwds['title']))
            else:
                self.__title = html.escape(text)

        # content + tags for presentation (e.g. __decl in class vars)
        # the div value is inserted into the div -- useful for images, etc.
        if 'div' in kwds:
            # clean potential closing tags / limit malicious code
            tag_value = re.sub(r"<\s*/\s*div\s*>", "", str(kwds['div']))
            tag_value = f"        <div{idd}{claz}{style}>{tag_value}</div>"
            self._content.append(AsIsText(tag_value))
        # text content is escaped and embedded in paragraph tag by default
        #     unless different tag is specified in kwds
        if text and 'title' not in kwds:
            tag = str(kwds['tag']) if 'tag' in kwds else "p"
            tag = tag if tag.strip() else "p"
            tag_open = f"<{tag}{idd}{claz}{style}>"
            tag_close = (
                f"</{tag}>" if tag.strip() not in self.void_elements else ""
            )
            self._content.append(
                AsIsText(tag_open + html.escape(text) + tag_close)
            )
        # NOTE that list and pre are placed below text to allow a compound
        #     add_declaration statement that includes text, tag, pre and/or
        #     list that places a paragraph above the formatted content to
        #     allow prose to describe the reported values
        # lists -- list should actually be a list of items as a str will parse
        #          into its constituent chars
        if 'list' in kwds:
            # value of enum is ignored but presence implies numbered list
            tag_value = "ol" if 'enum' in kwds else "ul"
            self._content.append(AsIsText(f"<{tag_value}{idd}{claz}{style}>"))
            for item in list(kwds['list']):
                item = html.escape(item)
                self._content.append(AsIsText(f"<li>{item}</li>"))
            self._content.append(AsIsText(f"</{tag_value}>"))
        # pre -- display preformatted text
        if 'pre' in kwds:
            # clean potential closing tags / limit malicious code
            tag_value = re.sub(r"<\s*/\s*pre\s*>", "", str(kwds['pre']))
            tag_value = f"<pre{idd}{claz}{style}>{tag_value}</pre>"
            self._content.append(AsIsText(tag_value))
        return

    def render(self) -> str:
        buf = io.StringIO()
        buf.write("<!DOCTYPE HTML>")
        buf.write("<html lang=\"en-US\">")
        buf.write("    <head>")
        buf.write("        <meta charset=\"UTF-8\">")
        buf.write(f"        <title>{self.__title}</title>")
        buf.write(
            f"        <script type=\"text/javascript\" src=\"https://cdn.pydata.org/bokeh/release/bokeh-{bokeh.__version__}.min.js\"></script>"
        )
        buf.write(
            f"        <script type=\"text/javascript\" src=\"https://cdn.pydata.org/bokeh/release/bokeh-widgets-{bokeh.__version__}.min.js\"></script>"
        )
        buf.write(
            f"        <script type=\"text/javascript\" src=\"https://cdn.pydata.org/bokeh/release/bokeh-tables-{bokeh.__version__}.min.js\"></script>"
        )
        for js in self.__js:
            buf.write(js)
        for css in self.__css:
            buf.write(css)
        buf.write("    </head>")
        buf.write("    <body>")
        # 20200102: write self.__decl for backwards compatibility
        for d in self.__decl:
            buf.write(d)
        # iff using add_declaration_inline(...) then declarations are
        #     rendered in order with add_primitive(...), tables, etc.
        self._render(buf)
        buf.write("    </body>")
        buf.write("</html>")
        return buf.getvalue()

    pass
