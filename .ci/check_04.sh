#! /usr/bin/env bash

# COPYRIGHT:
# Copyright (c) 2015-2022, California Institute of Technology ("Caltech").
# U.S. Government sponsorship acknowledged.
#
# All rights reserved.
#
# LICENSE:
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   - Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
#   - Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#
#   - Neither the name of Caltech nor its operating division, the Jet
# Propulsion Laboratory, nor the names of its contributors may be used to
# endorse or promote products derived from this software without specific
# prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# NTR:

. .ci/util.sh

state="pending" # "success" "pending" "failure" "error"
description="Verify legal content: copyright and license in all files"
context="continuous-integration/04/legal"

post_state "$context" "$description" "$state"

if current_state
then
    docker run --rm -e PYTHONPATH=${PWD}/Python -e USERNAME="$(whoami)" -v $PWD:$PWD -u $UID -w $PWD -i niessner/cit:$(cit_version) python3 <<EOF
import datetime
import os

def _format (text, length=79, prefix='', suffix='\n'):
    length = length - len (suffix)
    result = '\n'
    for line in text.split('\n'):
        newline = prefix + line
        while length < len (newline):
           l = newline [:length].rfind (' ')
           result += newline[:length if l < 0 else l].strip()+suffix 
           newline = prefix + newline[length if l < 0 else l:].strip()
           pass
        result += newline.strip() + suffix
        pass
    return result + prefix

def shell_style (text): return _format (text, prefix='# ')

with open ('COPYRIGHT.txt', 'rt') as f: cr = f.read()
with open ('LICENSE.txt', 'rt') as f: lic = f.read()
dl = cr.find ('2015-20')
cr = cr.replace (cr[dl:dl+9], 
                 '2015-{}'.format (datetime.datetime.now().year))
formatters = {'.hamlbars':_format, '.hbs':_format, '.html':_format,
              '.dot':_format, '.js':_format,
              '.py':_format, '.sh':shell_style}
legal = True
for p,dns,fns in os.walk ('.'):
    if any ([p.startswith ('./.{}'.format (d))
             for d in [ 'cache', 'git' ]]) : continue

    for fn in filter (lambda s:any ([s.endswith (suffix) for suffix in
                                    ('.py', '.sh', '.hbs',
                                     '.hamlbars', '.html', '.dot')] +
                                    [s.startswith ('Dockerfile.') and s[-1] != '~']),
                      fns):
       suffix = '.sh' if fn.startswith ('Dockerfile.') else fn[fn.rfind ('.'):]
       fn = os.path.join (p, fn)
       with open (fn, 'rt') as f: text = f.read()
       cprl = text.find ('COPY' + 'RIGHT:')
       licl = text.find ('LIC' + 'ENSE:')
       ntrl = text.find ('NT' + 'R:')

       if cprl < licl < ntrl:
           scr = formatters[suffix] (cr)
           slc = formatters[suffix] (lic)

           if text[licl+8:min (ntrl, licl+8+len(slc))] != slc:
               legal = False
               print ('license requires update', fn)
               text = text[:licl+8] + slc + text[ntrl:]
               pass
           if text[cprl+10:min (licl, cprl+10+len(scr))] != scr:
               legal = False
               print ('copyright requires update', fn)
               text = text[:cprl+10] + scr + text[licl:]
               pass

           if $#:
               with open (fn, 'tw') as f: f.write (text)
               pass
       else:
          print ('need to update', fn,
                 'with COPY' + 'RIGHT:, LIC' + 'ENSE:, NT' + 'R:')
          legal = False
          pass
       pass
    pass

if not legal:
    with open ('.ci/status.txt', 'tw') as f: f.write ('failure')
    pass
EOF
    [[ $# -eq 0 ]] && git checkout 
    state=`get_state`
fi

post_state "$context" "$description" "$state"
