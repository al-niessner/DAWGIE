'''encapsulate the python shelve file states

--
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

import datetime
import dawgie
import dawgie.context
import glob
import os


class LocalVersion(dawgie.Version):
    def __init__(self, version):
        if isinstance(version, str):
            version = [int(v) for v in version.split('.')]
        self._version_ = dawgie.VERSION(*version)
        return

    @property
    def version(self):
        return self._version_

    pass


def append(
    name: str,
    table: {},
    index: [],
    parent: int = None,
    ver: dawgie.Version = None,
) -> (bool, int, str):
    exists = False
    name = construct(name, parent, ver)
    if name not in table:
        table[name] = len(index)
        index.append(name)
        pass
    idx = table[name]
    exists = True
    return exists, idx, name


def construct(name: str, parent: int = None, ver: dawgie.Version = None) -> str:
    if parent is not None:
        name = str(parent) + ':parent___' + name
    if ver:
        name = name + '___version:' + ver.asstring()
    return name


def dissect(name: str) -> (int, str, dawgie.Version):
    if ':parent___' in name:
        parent, name = name.split(':parent___')
        parent = int(parent)
    else:
        parent = None

    if '___version:' in name:
        name, ver = name.split('___version:')
        ver = LocalVersion(ver)
    else:
        ver = None
    return parent, name, ver


def indexed(table: {}) -> []:
    return [t[0] for t in sorted(table.items(), key=lambda t: t[1])]


def make_staging_dir():
    t = datetime.datetime.now()
    # too error prone to fix and probably not much more readable anyway so
    # pylint: disable=consider-using-f-string
    tstring = "%s/%d-%d-%dT%d:%d" % (
        dawgie.context.data_stg,
        t.year,
        t.month,
        t.day,
        t.hour,
        t.minute,
    )
    os.system(f'mkdir {tstring}')
    return tstring


def prime_keys(prime_table):
    # because shelve key must be a string, pylint: disable=eval-used
    return [eval(k) for k in prime_table]


def rotated_files(index=None):
    path = dawgie.context.db_rotate_path
    if index is None:
        orig = glob.glob(f"{path}/{dawgie.context.db_name}.alg")
        orig += glob.glob(f"{path}/{dawgie.context.db_name}.prime")
        orig += glob.glob(f"{path}/{dawgie.context.db_name}.state")
        orig += glob.glob(f"{path}/{dawgie.context.db_name}.target")
        orig += glob.glob(f"{path}/{dawgie.context.db_name}.task")
        orig += glob.glob(f"{path}/{dawgie.context.db_name}.value")
        return orig
    orig = glob.glob(f"{path}/{index:d}.{dawgie.context.db_name}.alg")
    orig += glob.glob(f"{path}/{index:d}.{dawgie.context.db_name}.prime")
    orig += glob.glob(f"{path}/{index:d}.{dawgie.context.db_name}.state")
    orig += glob.glob(f"{path}/{index:d}.{dawgie.context.db_name}.target")
    orig += glob.glob(f"{path}/{index:d}.{dawgie.context.db_name}.task")
    orig += glob.glob(f"{path}/{index:d}.{dawgie.context.db_name}.value")
    return orig


def subset(from_table: {str: int}, name: str, parents: [int] = None) -> {}:
    '''extract a subset of table as a dictionary

    It behaves two different ways. If parnets is provided, then it will use
    util.construct() to generate the full name given the parents. If parents is
    not given, then it will simply use name.
    '''
    result = {}
    if parents:
        for parent in parents:
            surname = construct(name, parent)
            result.update(
                dict(
                    filter(
                        lambda t, sn=surname: t[0].startswith(sn),
                        from_table.items(),
                    )
                )
            )
            pass
        pass
    else:
        result.update(
            dict(
                filter(
                    lambda t, sn=name: t[0].startswith(sn), from_table.items()
                )
            )
        )
        pass
    return result
