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

import dawgie.context
import logging; log = logging.getLogger(__name__)
import os
import pickle
import shutil
import subprocess
import tempfile

def _extract (response):
    for pair in filter (lambda l:0 < len (l),
                        response.decode ('utf-8').split ('\n')):
        index = pair.find (' ')
        cksum = pair[:index]
        lc = cksum.strip()
        pass
    return lc

def decode (entry):
    with open (os.path.join (dawgie.context.data_dbs, entry), 'rb') as f:
        result = pickle.load (f)
        pass
    return result

def encode (value):
    fid,fn = tempfile.mkstemp (dir=dawgie.context.data_stg,
                               prefix='shelve_', suffix='.pkl')
    os.close (fid)
    with open (fn, 'wb') as f: pickle.dump (value, f, pickle.HIGHEST_PROTOCOL)
    os.chmod (fn, int ('0664', 8))  # -rw-rw-r--
    m = _extract (subprocess.check_output (['md5sum', '-b', fn]))
    s = _extract (subprocess.check_output (['sha1sum', '-b',  fn]))
    result = '_'.join ([m,s])
    return (fn,result)

def move (fn, result):
    nfn = os.path.join (dawgie.context.data_dbs, result)
    exists = os.path.exists (nfn)

    if exists: os.unlink (fn)
    else: shutil.move (fn, nfn)

    return result,exists

def rotate(path, orig, backup):
    # if current db is missing, then copy recent db
    # else shift db names down one
    if not orig:
        for i in sorted(backup.keys()):
            if backup[i]:
                log.warning("orig db missing, copying from db %d", i)
                for v in backup[i]:
                    t = v.split(".")[-1]
                    shutil.copy(v, f'{path}/{dawgie.context.db_name}.{t}')
                    pass
                break
        pass
    else:
        rotatedDb = sorted(backup.keys())
        stack = []
        for i in rotatedDb:
            if not backup[i]: break
            stack.append(i)
        for i in range(len(stack)):
            t = stack.pop()
            for v in backup[t]:
                ext = v.split(".")[-1]
                shutil.move(v, f'{path}/{t+1:d}.{dawgie.context.db_name}.{ext}')
        for v in orig:
            ext = v.split(".")[-1]
            shutil.copy(v, f'{path}/0.{dawgie.context.db_name}.{ext}')

    return

def verify (value):
    # pylint: disable=bare-except
    result = [False, False, False, False]
    result[0] = isinstance (value, dawgie.Value)
    try:
        result[1] = isinstance (value.bugfix(), int)
        result[2] = isinstance (value.design(), int)
        result[3] = isinstance (value.implementation(), int)
    except: pass
    return all (result)
