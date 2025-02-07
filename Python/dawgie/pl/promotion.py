'''
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

NTR:
'''

import dawgie.db
import dawgie.context
import dawgie.pl.dag
import dawgie.util
import logging

log = logging.getLogger(__name__)


class Engine:
    def __call__(
        self,
        values: [(str, bool)] = None,
        original: dawgie.pl.dag.Node = None,
        rid: int = None,
    ):
        arg_state = (values is not None, original is not None, rid is not None)

        if all(arg_state):  # new item to promote
            self.todo(original, rid, values)
        elif any(arg_state):  # error because its all or nothing
            log.error('Inconsistent arguments. Ignoring request.')
            log.debug('  values: %s', str(values))
            log.debug('  original: %s', str(original))
            log.debug('  run ID: %s', str(rid))
        else:
            self.do()

        return self.more()

    def __init__(self):
        self._ae = None
        self._organize = None
        self._todo = {}
        return

    def _append(self, algnode, runid, values):
        for child in algnode:
            if child.tag in self._todo:
                self._todo[child.tag][1].append(algnode)
                self._todo[child.tag][3].extend(values)
            else:
                self._todo[child.tag] = (child, [algnode], runid, values)
            pass
        return

    @property
    def ae(self) -> dawgie.pl.dag.Construct:
        return self._ae

    @ae.setter
    def ae(self, ae: dawgie.pl.dag.Construct):
        self._ae = ae

    def clear(self):
        self._todo.clear()

    def do(self):
        if dawgie.context.allow_promotion and self.ae is None:
            raise ValueError('AE is not set prior to data flow')
        if dawgie.context.allow_promotion and self.organize is None:
            raise ValueError('Organizer is not set prior to data flow')

        if dawgie.context.allow_promotion and self.more():
            values = sorted(
                self._todo.values(), key=lambda t: t[0].get('level')
            )
            child, parents, runid, values = values.pop(0)
            targets = {v.split('.')[1] for v in values}
            vals = {'.'.join(v.split('.')[2:]) for v in values}

            if len(targets) == 1:
                target_name = targets.copy().pop()
            else:
                raise ValueError(
                    f'Inconsistent targets for a single result {targets}'
                )

            inputs = set()
            outputs = self._ae[child.tag]
            # 1: does decendent require subset of values
            #  if no, then break
            for o in outputs:
                inputs.update(o.get('parents'))
            dependents = []
            for parent in parents:
                name = parent.tag + '.'
                dependents.extend(
                    (
                        d.tag
                        for d in filter(
                            lambda i, n=name: i.tag.startswith(n), inputs
                        )
                    )
                )
                pass

            if not set(dependents).issubset(vals):
                self._organize(
                    [child.tag],
                    runid,
                    targets,
                    'promotion not possible because one or '
                    + 'more inputs is new value',
                )
                return

            # 2: is the dependent or ancestors are schduled to run already
            #    or are running
            #  if yes, then break
            if _is_scheduled(child, targets):
                return

            # 3: find the consistent set of previous inputs for each output
            #    in this child
            juncture = dawgie.db.consistent(
                _translate(inputs), _translate(outputs), target_name
            )

            # 4: are all of the inputs to dependent the same
            #    if no, schedule dependent and break
            if not juncture or not all(juncture):
                self._organize(
                    [child.tag],
                    runid,
                    targets,
                    'promotion not possible because ' + 'no juncture found',
                )
                return

            # 5: promote decendent state vectors
            if not dawgie.db.promote(juncture, runid):
                self._organize(
                    [child.tag], runid, targets, 'promotion failed to insert'
                )
                return

            # 6: add decendent to todo list
            self._append(child, runid, _outs2vals(runid, target_name, outputs))
        elif not dawgie.context.allow_promotion:
            self.clear()
        return

    def more(self) -> bool:
        return 0 < len(self._todo)

    @property
    def organize(self):
        return self._organize

    @organize.setter
    def organize(self, organizer):
        '''a function used to organize the work to be done

        Should have the same arguments as dawgie.pl.schedule.organize.
        In fact, the default behavior of the pipeline is to use
        dawgie.pl.schedule.organize
        '''
        self._organize = organizer
        return

    def todo(
        self,
        original: dawgie.pl.dag.Node = None,
        rid: int = None,
        values: [(str, bool)] = None,
    ):
        if not all((v[1] for v in values)):
            self._append(
                original,
                rid,
                [value for value, _isnew in filter(lambda t: not t[1], values)],
            )
            pass
        return

    pass


def _is_scheduled(node: dawgie.pl.dag.Node, targets: {str}) -> bool:
    # issubset works because do() reduces targets to length of 1
    result = any(
        [
            targets.issubset(node.get('do')),
            targets.issubset(node.get('doing')),
            targets.issubset(node.get('todo')),
        ]
    )

    if not result:
        for parent in node.get('parents'):
            result |= _is_scheduled(parent, targets)
            pass
        pass
    return result


def _outs2vals(runid: int, tn: str, outs: [dawgie.pl.dag.Node]):
    return ['.'.join([str(runid), tn, o.tag]) for o in outs]


def _translate(nodes: [dawgie.pl.dag.Node]) -> [dawgie.db.REF]:
    result = []
    for n in nodes:
        tn, an, sn, vn = n.tag.split('.')
        a = n.get('alg')
        s = a.sv_as_dict()[sn]
        v = s[vn]
        result.append(
            dawgie.db.REF(
                tid=dawgie.db.ID(tn, None),
                aid=dawgie.db.ID(an, a),
                sid=dawgie.db.ID(sn, s),
                vid=dawgie.db.ID(vn, v),
            )
        )
        pass
    return result
