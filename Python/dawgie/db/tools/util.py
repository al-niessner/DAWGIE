'''General utility functions for all of the DB tools

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

def add_arguments (ap):
    ap.add_argument ('-r', '--run-id', default=None,required=False,type=int,
                     help='The run ID to match where None means any [%(default)s]')
    ap.add_argument ('-T', '--target-name', default=None,required=False,type=str,
                     help='The target name to match where None means any [%(default)s]')
    ap.add_argument ('-t', '--task-name', default=None,required=False,type=str,
                     help='The task name to match where None means any [%(default)s]')
    ap.add_argument ('-a', '--alg-name', default=None,required=False,type=str,
                     help='The algorithm name to match where None means any [%(default)s]')
    ap.add_argument ('-s', '--state-vector-name', default=None, required=False,
                     type=str, help='The state vector name to match where None means any [%(default)s]')
    ap.add_argument ('-v', '--value-name',default=None,required=False,type=str,
                     help='The value name to match where None means any [%(default)s]')
    return
