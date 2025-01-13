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

import argparse
import dawgie.context
import dawgie.db
import dawgie.pl.dag
import dawgie.pl.scan
import logging
import os


def _dir(dn: str):
    if not os.path.isdir(dn):
        raise ValueError(f'The specified value {dn} is not a directory')
    return dn


known = set()


def pt(task, text=''):
    text += task.tag

    if task.tag not in known and task:
        known.add(task.tag)
        for c in task:
            text = pt(c, text + ' -> ')
    return text


ap = argparse.ArgumentParser(
    description='Build the task, algorithm, state vector, and value trees for the AE and write them to --output-dir.'
)
# ignore tools that use similar arguments
# pylint: disable=duplicate-code
ap.add_argument(
    '-O',
    '--output-dir',
    required=True,
    type=_dir,
    help='directory to write the SVG files to',
)
ap.add_argument(
    '-v',
    '--verbose',
    action='store_true',
    default=False,
    help='display processing information',
)
# pylint: enable=duplicate-code
dawgie.context.add_arguments(ap)
args = ap.parse_args()

if args.verbose:
    logging.basicConfig(level=logging.DEBUG)

dawgie.context.override(args)
dawgie.db.open()
factories = dawgie.pl.scan.for_factories(
    dawgie.context.ae_base_path, dawgie.context.ae_base_package
)
dag = dawgie.pl.dag.Construct(factories)
print('root count:', len(dag.tt))
for tt in dag.tt:
    print(pt(tt))
with open(os.path.join(args.output_dir, 'av.svg'), 'wb') as f:
    f.write(dag.av)
with open(os.path.join(args.output_dir, 'sv.svg'), 'wb') as f:
    f.write(dag.svv)
with open(os.path.join(args.output_dir, 'tv.svg'), 'wb') as f:
    f.write(dag.tv)
with open(os.path.join(args.output_dir, 'vv.svg'), 'wb') as f:
    f.write(dag.vv)
