''' unit testing implementation of dawgie.db

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

NTR: 49811
'''

# pylint: disable=redefined-builtin,too-many-arguments,unused-argument

from dawgie.db import REF

def add (target_name:str)->bool: return False

def archive (done): raise NotImplementedError()

def close(): return

def connect (alg, bot, tn): raise NotImplementedError()

def consistent (inputs:[REF], outputs:[REF], target_name:str)->(): raise NotImplementedError()

def copy (dst, method, gateway): raise NotImplementedError()

def gather (anz, ans): raise NotImplementedError()

def metrics()->'[dawgie.db.METRIC_DATA]': raise NotImplementedError()

def next(): raise NotImplementedError()

def open(): raise NotImplementedError()

def promote (juncture:(), runid:int): raise NotImplementedError()

def remove(runid, tn, taskn, algn, svn, vn): raise NotImplementedError()

def reopen(): raise NotImplementedError()

def retreat (reg, ret): raise NotImplementedError()

def targets(): return ['a','b','c','d','e','f','g']

def trace (task_alg_names): raise NotImplementedError()

def update (tsk, alg, sv, vn, v): raise NotImplementedError()

def versions(): raise NotImplementedError()

def view_locks(): raise NotImplementedError()
