'''Naming helpers

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
import logging


def task_name(factory):
    '''Compute the pipeline specified prefix for any dawgie.Task

    Given the factory function for a list of dawgie.Task, compute the prefix
    to allow algorithms to share names sensibly. The rest of the name is just
    the index of the task in the list.
    '''
    cnt = len(dawgie.context.ae_base_package.split('.'))
    return '.'.join(factory.__module__.split('.')[cnt:])


def verify_name(o, err=False):
    '''Check the name of an object meets the naming convention

    The architecture generate a full name by ".".join (elements). Hence, the
    name cannot contain the special character ".". This function checks the
    dawgie.Algorithm.name() and dawgie.StateVector.name(). In the case
    of dawgie.StateVector, it also checks all of the keys(). Details of
    failures will be sent to logging.critical().

    o : the object to check
    err : if True, then raise a ValueError otherwise when check fails

    return True when o.name().find (".") < 0 and same for
                dawgie.StateVector.keys()
    '''
    log = logging.getLogger(__file__)
    result = o.name().find(".") < 0

    if not result:
        log.critical('The name "%s" contains the special character "."', o.name)
    if isinstance(o, dawgie.StateVector):
        for name, state in [(k, k.find('.') < 0) for k in o.keys()]:
            result &= state
            if not state:
                log.critical(
                    'The name "%s" contains the special character "."', name
                )
            pass
        pass
    if err and not result:
        raise ValueError('The name(s) contains the special character "."')
    return result
