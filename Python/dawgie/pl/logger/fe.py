'''
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

NTR: 49811
'''

import dawgie.context
import logging.handlers

INSTANCE = None


class Handler(logging.handlers.BufferingHandler):
    def __init__(self):
        logging.handlers.BufferingHandler.__init__(
            self, dawgie.context.log_capacity
        )
        self.setFormatter(
            logging.Formatter(
                '%(asctime)s;\n;'
                + '%(name)s;\n;'
                + '%(levelname)s;\n;'
                + '%(message)s'
            )
        )
        return

    def emit(self, record):
        self.buffer.insert(0, record)
        while self.capacity <= len(self.buffer):
            self.buffer.pop()
        return

    def shouldFlush(self, record):
        return False

    pass


def remembered():
    history = []
    for r in INSTANCE.buffer:
        details = INSTANCE.format(r).split(';\n;')
        history.append(
            {
                'timeStamp': details[0],
                'name': details[1],
                'level': details[2],
                'message': '\n\n'.join(details[3:]),
            }
        )
        pass
    return history
