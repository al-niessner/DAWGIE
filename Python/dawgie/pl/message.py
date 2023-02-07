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

import collections
import enum
import pickle
import socket
import struct

MSG = collections.namedtuple ('MSG', ['context',
                                      'factory',
                                      'incarnation',
                                      'jobid',
                                      'ps_hint',
                                      'revision',
                                      'runid',
                                      'success',
                                      'target',
                                      'timing',
                                      'type',
                                      'values'])

@enum.unique
class Type(enum.Enum):
    cloud = 5
    register = 0
    response = 1
    status = 4
    task = 2
    wait = 3
    pass

# pylint: disable=too-many-arguments
def make (ctxt:bytes=None,
          fac=None,
          inc:int=None,
          jid:str=None,
          psh:int=None,
          rev:str=None,
          rid:int=None,
          suc:bool=None,
          target:str=None,
          tim:{}=None,
          typ:Type=Type.wait,
          val=None)->MSG: return MSG(context=ctxt,
                                     factory=fac,
                                     incarnation=inc,
                                     jobid=jid,
                                     ps_hint=psh,
                                     revision=rev,
                                     runid=rid,
                                     success=suc,
                                     target=target,
                                     timing=tim,
                                     type=typ,
                                     values=val)

def dumps (m:MSG)->bytes: return pickle.dumps (m, pickle.HIGHEST_PROTOCOL)
def loads (b:bytes)->MSG: return pickle.loads (b)

def receive (s:socket.socket)->MSG:
    buf = b''
    while len (buf) < 4: buf += s.recv (4 - len (buf))
    l = struct.unpack ('>I', buf)[0]
    buf = b''
    while len (buf) < l: buf += s.recv (l - len (buf))
    return loads (buf)

def send (m:MSG, s:socket.socket)->None:
    stream = dumps (m)
    return s.sendall (struct.pack ('>I', len (stream)) + stream)
