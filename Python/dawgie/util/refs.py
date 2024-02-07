'''Reference helpers to turn everything into a [dawgie.V_REF]

--
COPYRIGHT:
Copyright (c) 2015-2024, California Institute of Technology ("Caltech").
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

import dawgie
import dawgie.util.names

def algref2svref (ref:dawgie.ALG_REF)->[dawgie.SV_REF]:
    return [dawgie.SV_REF(factory=ref.factory, impl=ref.impl, item=sv)
            for sv in ref.impl.state_vectors()]

def as_vref (references:[dawgie.ALG_REF, dawgie.SV_REF, dawgie.V_REF]):
    for reference in references:
        if isinstance (reference, dawgie.V_REF): yield reference
        if isinstance (reference, dawgie.SV_REF):
            for vref in svref2vref (reference): yield vref
            pass
        if isinstance (reference, dawgie.ALG_REF):
            for svref in algref2svref (reference):
                for vref in svref2vref (svref): yield vref
                pass
            pass
        pass
    return

def svref2vref (ref:dawgie.SV_REF)->[dawgie.V_REF]:
    return [dawgie.V_REF(factory=ref.factory, impl=ref.impl, item=ref.item,
                         feat=key) for key in ref.item]

def vref_as_name (vref:dawgie.V_REF)->str:
    return '.'.join ([dawgie.util.names.task_name (vref.factory),
                      vref.impl.name(), vref.item.name(), vref.feat])
