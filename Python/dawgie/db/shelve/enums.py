'''Enumerations needed for distributing the shelve database

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

import enum


class Func(enum.IntEnum):
    # enums should not scream at you so pylint: disable=invalid-name
    acquire = 0  # acquire a lock to the database
    dbcopy = 1  # copy the database to a new location (backup)
    get = 2  # get the value of the table for the key
    table = 3  # get a table in the database
    release = 4  # release a lock being held on the database
    set = 5  # set the value of the table for the key
    upd = 6  # update the table[key], returning True if it exists else False
    pass


class Method(enum.Enum):
    # enums should not scream at you so pylint: disable=invalid-name
    connector = "connector"
    rsync = "rsync"
    scp = "scp"
    cp = "cp"
    pass


class Mutex(enum.IntEnum):
    # enums should not scream at you so pylint: disable=invalid-name
    lock = 0
    unlock = 1
    pass


class Table(enum.IntEnum):
    # enums should not scream at you so pylint: disable=invalid-name
    alg = 0
    prime = 1
    state = 2
    target = 3
    task = 4
    value = 5
    pass
