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
import datetime
import enum

class LockRequest(enum.Enum):
    lrqb = "Lock_Request_Begin"
    lrqe = "Lock_Request_End"
    laqb = "Lock_Acquire_Begin"
    laqe = "Lock_Acquire_End"
    lrlb = "Lock_Release_Begin"
    lrle = "Lock_Release_End"
    pass

class TaskLock:
    def __init__(self, tn:str, action:str):
        self.tn = tn
        self.action = action
        self.starttime = datetime.datetime.utcnow()
        self.lasttime_delta = 0
        self.state = "busy"
        pass

    def done(self): self.set_state("done")

    def get_delta_time(self):
        return (datetime.datetime.utcnow() - self.starttime).total_seconds()

    def get_duration(self):
        if self.state == "done":
            return self.lasttime_delta
        self.lasttime_delta = self.get_delta_time()
        return self.lasttime_delta

    def set_state(self, s:str):
        if s in ["done","busy"]:
            self.state = s
            self.lasttime_delta = self.get_delta_time()
            pass
        pass

    def to_string(self):
        return f"{self.starttime.isoformat()} {self.tn} {self.action.value}"
    pass

class TaskLockEngine:
    def __init__(self):
        self.queue = collections.OrderedDict()
        pass

    def add_task(self, name:str, action:str):
        self.queue[(name,action)] = TaskLock(name, action)
        pass

    def end_task(self, name:str, action:str):
        self.queue[(name,action)].done()
        pass

    def get_progress(self):
        s = []
        for i in reversed(self.queue):
            s.append(self.queue[i].to_string())
            pass
        return s

    def view_progress(self):
        return {"tasks": self.get_progress()}
    pass
