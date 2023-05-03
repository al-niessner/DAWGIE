'''encapsulate the python shelve file states

--
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

import collections
import dawgie.context
import dawgie.db.lockview
import os
import shelve

from . import util
from .enums import Table

class DBI:
    '''contains the shelve dictionary-file and tracks their state'''
    def __init__(self):
        if not hasattr (self, '_DBI__tables'):
            self.__indices = self.__Group(**{n:None for n in self.__names})
            self.__reopened = False
            self.__tables = self.__Group(**{n:None for n in self.__names})
            self.__task_engine = None
            pass
        return

    def __new__(cls):
        if not hasattr (cls, '_DBI__myself'):
            cls.__names = [tab.name for tab in sorted (Table,
                                                       key=lambda e:e.value)]
            cls.__Group = collections.namedtuple ('Group', cls.__names)
            cls.__myself = super(DBI, cls).__new__(cls)
            pass
        return cls.__myself

    def close(self):
        '''close all the dictionary-files'''
        self.__reopened = False
        for table in self.__tables:
            if table is not None: table.close()
            pass
        self.__indices = self.__Group(**{n:None for n in self.__names})
        self.__reopened = False
        self.__tables = self.__Group(**{n:None for n in self.__names})
        self.__task_engine = None
        return

    def copy(self)->{}:
        return {name:dict(table) for name,table in zip(self.__names,
                                                       self.__tables)}

    def open(self):
        '''open all the dictionary-files'''
        if not self.is_open:
            db,idx = {},{}
            path = os.path.join (dawgie.context.db_path, dawgie.context.db_name)
            for name in self.__names:
                db[name] = shelve.open ('.'.join ([path, name]),'c')
                idx[name] = util.indexed (db[name])
                pass
            self.__indices = self.__Group(**idx)
            self.__tables = self.__Group(**db)
            self.__task_engine = dawgie.db.lockview.TaskLockEngine()
            pass
        return

    def reopen(self):
        '''distributed objects do a reopen rather than an open'''
        self.__reopened = True
        return self.is_open

    @staticmethod
    def save_as (db:{str:{}}, path:str):
        '''save a shelve db to a new path'''
        for name,table in db.items():
            dbt = shelve.open ('.'.join ([path, name]), 'c')
            dbt.update (table)
            dbt.close()
            pass
        return

    @property
    def is_open(self)->bool:
        '''determine if we have access to the database'''
        return self.__reopened or all (table is not None
                                       for table in self.__tables)
    @property
    def is_reopened(self)->bool:
        '''determine if was a reopen or opened locally'''
        return self.__reopened
    @property
    def indices(self): return self.__indices
    @property
    def tables(self): return self.__tables
    @property
    def task_engine(self): return self.__task_engine
    pass
