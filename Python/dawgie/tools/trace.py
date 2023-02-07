#! /usr/bin/env python3
'''
COPYRIGHT:
Copyright (c) 2015-2023, California Institute of Technology ("Caltech").
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

# pylint: disable=import-self

import base64
import io
import logging
import numpy
import os
import pydot
import shutil
import sys
import tempfile
import webbrowser

_template_image = '''
<div>
<h3>{title:s}</h3>
<img src="data:image/svg+xml;base64,{tree:s}">
<img src="data:image/png;base64,{chart:s}">
</div>
'''
_template_page = """
<!DOCTYPE html>
<html>
  <head>
    <meta content='text/html; charset=US-ASCII' http-equiv='Content-Type'>
    <meta charset='utf-8'>
    <meta content='IE=edge,chrome=1' http-equiv='X-UA-Compatible'>
    <title>Trace Report</title>
  </head>
  <body id='top'>
<h1>Trace Report</h1>
<h2>Statistics</h2>
<ol>
<li>Number of Roots: {nroots:d}</li>
<li>Number of Routes: {nroutes:d}</li>
<li>Number of Paths: {npaths:d}</li>
</ol>
<h2>Charts</h2>
{images:s}
  </body>
</html>
"""

# pylint: disable=dangerous-default-value,protected-access
def _trace (t, path=[], routes={}):
    path = path.copy() + [t.tag]

    if list(t):
        for c in filter (lambda n,this=t.tag:n.tag != this, t):\
            _trace (c, path.copy(), routes)
        pass
    elif t.get ('shape') != dawgie.pl.dag.Shape.rectangle:
        key = (path[0],path[-1])
        if key not in routes: routes[key] = []
        routes[key].append (path)
        pass
    return routes

def main (fn:str=None, at=None):
    '''Find and graph all targets through the algorithm dependency tree

    at : algorithm tree from dawgie.pl.dag.Construct()
    fn : filename to store the diagram and when None, display it.
    '''
    # pylint: disable=too-many-branches,too-many-locals,too-many-statements
    # control matplotlib loading so pylint: disable=import-outside-toplevel
    import matplotlib
    import matplotlib.pyplot

    if at is None:
        factories = dawgie.pl.scan.for_factories(dawgie.context.ae_base_path,
                                                 dawgie.context.ae_base_package)
        at = dawgie.pl.dag.Construct(factories).at
        pass

    charts = {}
    images = ''
    routes = {}
    traces = {}
    for root in at: routes.update (_trace (root))
    for key in sorted (routes, key='.'.join):
        algs = set()
        traces[key] = {}
        for path in routes[key]: algs.update (path)
        traces[key] = dawgie.db.trace (algs)
        pass
    for key,route in routes.items():
        last = []
        rank = {}
        for tn in sorted (traces[key]):
            if not rank:
                for tan in traces[key][tn].keys():
                    rank[tan] = max([path.index (tan) if tan in path else 0
                                     for path in route])
                    pass
                rank = {tan:i for i,(tan,r) in enumerate
                        (sorted (rank.items(), key=lambda x:x[1]))}
                algs = [i[0] for i in sorted (rank.items(), key=lambda x:x[1])]
                pass

            last.append (0)
            for tan,r in sorted (rank.items(), key=lambda x:x[1]):
                if traces[key][tn][tan] is not None: last[-1] = r
                pass
            pass
        charts[key] = matplotlib.pyplot.figure(figsize=(9,6))
        sp = charts[key].add_subplot (111)
        sp.barh (numpy.arange (len (traces[key])), last)
        matplotlib.pyplot.xticks (numpy.arange (len (rank)),
                                  [i[0] for i in sorted (rank.items(),
                                                         key=lambda x:x[1])],
                                  rotation=90)
        matplotlib.pyplot.yticks (numpy.arange (len (traces[key])),
                                  sorted (traces[key].keys()))
        pass
    fid,tfn = tempfile.mkstemp ('.html','trace')
    os.close (fid)
    av = pydot.Dot(graph_type='digraph', rank='same')
    for r in at: r._reset()
    for r in at: r.graph (av)
    with open (tfn, 'tw', encoding='UTF-8') as ff:
        for key in sorted (routes, key='.'.join):
            br = io.BytesIO()
            charts[key].savefig (br)
            names = set()
            for path in routes[key]: names.update (path)
            for n in av.get_nodes():
                if n.get_name()[1:-1] in names:
                    n.set_style ('filled')
                    n.set_fillcolor ('lawngreen')
                else:
                    n.set_style ('filled')
                    n.set_fillcolor ('white')
                    pass
                pass
            fid,ttfn = tempfile.mkstemp()
            os.close (fid)
            av.write_svg (ttfn)
            with open (ttfn, 'br') as fff: tree = fff.read()
            os.unlink (ttfn)
            images += _template_image.format \
                      (chart=base64.encodebytes (br.getvalue()).decode(),
                       title=key[0] + ' -> ' + key[1],
                       tree=base64.encodebytes (tree).decode())
            pass
        ff.write (_template_page.format (images=images,
                                         npaths=sum ([len (v) for v in
                                                      routes.values()]),
                                         nroots=len (at),
                                         nroutes=len (routes)))
        pass

    if fn:
        if not os.path.isdir (os.path.dirname (fn)): \
           os.makedirs (os.path.dirname (fn))
        shutil.move (tfn, fn)
    else: webbrowser.open_new_tab ('file://' + tfn)

    return

if __name__ == '__main__':
    # main blocks always look the same; pylint: disable=duplicate-code
    root_dir = os.path.dirname (__file__)
    for i in range(3): root_dir = os.path.join (root_dir, '..')
    root_dir = os.path.abspath (root_dir)
    sys.path.insert (0,root_dir)

    import argparse
    import dawgie.context
    import dawgie.db
    import dawgie.pl.dag
    import dawgie.pl.scan
    import dawgie.tools.trace
    import dawgie.util

    ap = argparse.ArgumentParser(description='Follow targets through the pipeline and display the results.')
    ap.add_argument ('-f', '--file-name', default=None, required=False,
                     help='file name to write the report -- a temp file will be used and displayed in your browser is none is given')
    ap.add_argument ('-l', '--log-file', default='trace.log', required=False,
                     help='a filename to put all of the log messages into [%(default)s]')
    ap.add_argument ('-L', '--log-level', default=logging.ERROR, required=False,
                     type=dawgie.util.log_level,
                     help='set the verbosity that you want where a smaller number means more verbose [logging.ERROR]')
    dawgie.context.add_arguments (ap)
    args = ap.parse_args()
    dawgie.context.log_level = args.log_level
    dawgie.context.override (args)
    dawgie.db.open()
    dawgie.tools.trace.main(fn=args.file_name)
    dawgie.db.close()
else:
    import dawgie.context
    import dawgie.db
    import dawgie.pl.dag
    import dawgie.pl.scan
    import dawgie.util
    pass
