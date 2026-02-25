'''
--
COPYRIGHT:
Copyright (c) 2015-2026, California Institute of Technology ("Caltech").
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

NTR: 49811
'''

import datetime
import dawgie.context
import json
import os


def append(entry: {}):
    if not all(
        key in entry
        for key in [
            'changeset',
            'runid',
            'status',
            'target',
            'task',
            'timing',
            'version',
        ]
    ):
        raise TypeError(
            'does not look like an execution mesage because it is missing expected keys'
        )
    for key, value in entry['timing'].items():
        if isinstance(value, datetime.datetime):
            entry[key] = value.isoformat(sep=' ')
    entries = []
    journal = os.path.join(
        dawgie.context.data_dbs,
        'chronicles',
        entry['timing']['started'].split(' ')[0].replace('-', os.path.sep),
    )
    if not os.path.isdir(journal):
        os.makedirs(journal, 0o755, True)
    journal = os.path.join(journal, f'{entry["runid"]}.json')
    if os.path.isfile(journal):
        with open(journal, 'rt', encoding='utf-8') as file:
            entries = json.load(file)
    entries.append(entry)
    with open(journal, 'tw', encoding='utf-8') as file:
        json.dump(entries, file, indent=2)
