'''the methods to facet/filter given user constrants

COPYRIGHT:
Copyright (c) 2015-2026, California Institute of Technology ("Caltech").
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

import dawgie.db

from dawgie.db.basis import Params
from dawgie.fe.basis import build_return_object, db_param_convert


def alg(
    runids: [str] = None,
    targets: [str] = None,
    tasks: [str] = None,
    svs: [str] = None,
):
    '''facet the algorithm name

    All parameters must be a string or list with content or None. An empty list
    will cause an error in later processing.
    '''
    # pylint: disable=duplicate-code
    engine = dawgie.db.search()
    parameters = Params(
        runids=runids[0] if runids and runids[0] else None,
        targets=db_param_convert(targets),
        tasks=db_param_convert(tasks),
        algs=[],
        svs=db_param_convert(svs),
        vals=None,
    )
    return build_return_object(engine.facet(parameters))


def sv(
    runids: [str] = None,
    targets: [str] = None,
    tasks: [str] = None,
    algs: [str] = None,
):
    '''facet the state vector name

    All parameters must be a string or list with content or None. An empty list
    will cause an error in later processing.
    '''
    # pylint: disable=duplicate-code
    engine = dawgie.db.search()
    parameters = Params(
        runids=runids[0] if runids and runids[0] else None,
        targets=db_param_convert(targets),
        tasks=db_param_convert(tasks),
        algs=db_param_convert(algs),
        svs=[],
        vals=None,
    )
    return build_return_object(engine.facet(parameters))


def task(
    runids: [str] = None,
    targets: [str] = None,
    algs: [str] = None,
    svs: [str] = None,
):
    '''facet the task name

    All parameters must be a string or list with content or None. An empty list
    will cause an error in later processing.
    '''
    # pylint: disable=duplicate-code
    engine = dawgie.db.search()
    parameters = Params(
        runids=runids[0] if runids and runids[0] else None,
        targets=db_param_convert(targets),
        tasks=[],
        algs=db_param_convert(algs),
        svs=db_param_convert(svs),
        vals=None,
    )
    return build_return_object(engine.facet(parameters))


def target(
    runids: [str] = None,
    tasks: [str] = None,
    algs: [str] = None,
    svs: [str] = None,
):
    '''facet the target name

    All parameters must be a string or list with content or None. An empty list
    will cause an error in later processing.
    '''
    # pylint: disable=duplicate-code
    engine = dawgie.db.search()
    parameters = Params(
        runids=runids[0] if runids and runids[0] else None,
        targets=[],
        tasks=db_param_convert(tasks),
        algs=db_param_convert(algs),
        svs=db_param_convert(svs),
        vals=None,
    )
    return build_return_object(engine.facet(parameters))
