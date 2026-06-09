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

import dawgie.context
import json
import os

from datetime import UTC, datetime, timedelta


def _load(after: datetime, before: datetime, journal: str, succeeded: bool):
    entries = []
    status = 'success' if succeeded else 'failure'
    for fn in filter(
        lambda fn: fn.endswith('.json'), os.listdir(journal)
    ):
        jsonfile = os.path.join(journal, fn)
        with open(jsonfile, 'rt', encoding='utf-8') as file:
            for entry in json.load(file):
                completed = datetime.fromisoformat(entry['timing']['completed'])
                if after < completed < before and entry['status'] == status:
                    entries.append(entry)
    entries.sort(key=_most_recent_first, reverse=True)
    return entries


def _most_recent_first(entry):
    return (
        entry['timing']['completed'],
        int(entry['runid']),
        entry['target'],
        entry['task'],
    )


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
        if isinstance(value, datetime):
            entry['timing'][key] = value.isoformat(sep=' ')
    entries = []
    journal = os.path.join(
        dawgie.context.data_dbs,
        'chronicles',
        entry['timing']['completed'].split(' ')[0].replace('-', os.path.sep),
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


def find(
    after: datetime = None,
    before: datetime = None,
    limit: int = None,
    succeeded: bool = True,
):
    '''Find the failed/succeeded tasks between two dates to a limit

    after - the date time the entries completion time should be after
    before - the date time the entries completion time should be before
    limit - total number of entries to be returned with None meaning unbounded

    Resulting list in youngest to oldest with the length of the list being
    less than or equal to the limit.

    Will throw error if after, before, and limit are None.
    '''
    if all(a is None for a in [after, before, limit]):
        raise ValueError('all arguments are None: after, before, limit')
    after = datetime(1980, 1, 1, tzinfo=UTC) if after is None else after
    before = datetime.now(UTC) if before is None else before
    entries = []
    one = timedelta(seconds=1)
    oneday = timedelta(days=1)
    while (limit is None or len(entries) < limit) and before > after:
        journal = os.path.join(
            dawgie.context.data_dbs, 'chronicles', str(before.year)
        )
        if os.path.isdir(journal):
            journal = os.path.join(journal, f'{before.month:02d}')
            if os.path.isdir(journal):
                journal = os.path.join(journal, f'{before.day:02d}')
                if os.path.isdir(journal):
                    entries.extend(_load(after, before, journal, succeeded))
                before = before - oneday
            else:
                before = datetime(before.year, before.month, 1, tzinfo=UTC) - one
        else:
            before = datetime(before.year, 1, 1, tzinfo=UTC) - one
    return entries[:limit]
