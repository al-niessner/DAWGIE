'''

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

import dawgie.context
import dawgie.fe.submit
import dawgie.pl.state
import unittest

from transitions.core import MachineError


class StateTransitions(unittest.TestCase):
    '''verify that the FSM always changes states correctly

    Except dawgie.fe.submit, all of the state changes are in dawgie.pl.state.
    The most likely problems are in dawgie.fe.submit because it changes state
    asynchronously from dawgie.pl.state. While nothing specifically wrong with
    being asynchronous (should be good given twisted) it is a point of change
    and contention.
    '''

    def test_archiving(self):
        dawgie.context.fsm = dawgie.pl.state.FSM(
            doctest_=True, initial_state='archiving'
        )
        with self.assertRaises(MachineError):
            dawgie.context.fsm.archiving_trigger()
        with self.assertRaises(MachineError):
            dawgie.context.fsm.contemplation_trigger()
        with self.assertRaises(MachineError):
            dawgie.context.fsm.gitting_trigger()
        with self.assertRaises(MachineError):
            dawgie.context.fsm.loading_trigger()
        with self.assertRaises(MachineError):
            dawgie.context.fsm.starting_trigger()
        with self.assertRaises(MachineError):
            dawgie.context.fsm.update_trigger()
        dawgie.context.fsm.running_trigger()
        self.assertEqual('running', dawgie.context.fsm.state)
        dawgie.context.fsm = dawgie.pl.state.FSM(
            doctest_=True, initial_state='archiving'
        )
        dawgie.context.fsm.updating_trigger()
        self.assertEqual('running', dawgie.context.fsm.state)

    def test_gitting(self):
        dawgie.context.fsm = dawgie.pl.state.FSM(
            doctest_=True, initial_state='gitting'
        )
        with self.assertRaises(MachineError):
            dawgie.context.fsm.archiving_trigger()
        with self.assertRaises(MachineError):
            dawgie.context.fsm.contemplation_trigger()
        with self.assertRaises(MachineError):
            dawgie.context.fsm.gitting_trigger()
        with self.assertRaises(MachineError):
            dawgie.context.fsm.loading_trigger()
        with self.assertRaises(MachineError):
            dawgie.context.fsm.starting_trigger()
        with self.assertRaises(MachineError):
            dawgie.context.fsm.update_trigger()
        with self.assertRaises(MachineError):
            dawgie.context.fsm.updating_trigger()
        dawgie.context.fsm.running_trigger()
        self.assertEqual('running', dawgie.context.fsm.state)

    def test_loading(self):
        dawgie.context.fsm = dawgie.pl.state.FSM(
            doctest_=True, initial_state='loading'
        )
        with self.assertRaises(MachineError):
            dawgie.context.fsm.archiving_trigger()
        with self.assertRaises(MachineError):
            dawgie.context.fsm.gitting_trigger()
        with self.assertRaises(MachineError):
            dawgie.context.fsm.loading_trigger()
        with self.assertRaises(MachineError):
            dawgie.context.fsm.running_trigger()
        with self.assertRaises(MachineError):
            dawgie.context.fsm.starting_trigger()
        with self.assertRaises(MachineError):
            dawgie.context.fsm.update_trigger()
        with self.assertRaises(MachineError):
            dawgie.context.fsm.updating_trigger()
        dawgie.context.fsm.contemplation_trigger()
        self.assertEqual('running', dawgie.context.fsm.state)

    def test_running(self):
        dawgie.context.fsm = dawgie.pl.state.FSM(
            doctest_=True, initial_state='running'
        )
        with self.assertRaises(MachineError):
            dawgie.context.fsm.loading_trigger()
        with self.assertRaises(MachineError):
            dawgie.context.fsm.running_trigger()
        with self.assertRaises(MachineError):
            dawgie.context.fsm.starting_trigger()
        with self.assertRaises(MachineError):
            dawgie.context.fsm.updating_trigger()
        dawgie.context.fsm.archiving_trigger()
        self.assertEqual('running', dawgie.context.fsm.state)
        dawgie.context.fsm = dawgie.pl.state.FSM(
            doctest_=True, initial_state='running'
        )
        dawgie.context.fsm.gitting_trigger()
        self.assertEqual('gitting', dawgie.context.fsm.state)
        dawgie.context.fsm = dawgie.pl.state.FSM(
            doctest_=True, initial_state='running'
        )
        dawgie.context.fsm.update_trigger()
        self.assertEqual('running', dawgie.context.fsm.state)

    def test_starting(self):
        dawgie.context.fsm = dawgie.pl.state.FSM(
            doctest_=True, initial_state='starting'
        )
        with self.assertRaises(MachineError):
            dawgie.context.fsm.archiving_trigger()
        with self.assertRaises(MachineError):
            dawgie.context.fsm.contemplation_trigger()
        with self.assertRaises(MachineError):
            dawgie.context.fsm.gitting_trigger()
        with self.assertRaises(MachineError):
            dawgie.context.fsm.loading_trigger()
        with self.assertRaises(MachineError):
            dawgie.context.fsm.running_trigger()
        with self.assertRaises(MachineError):
            dawgie.context.fsm.update_trigger()
        with self.assertRaises(MachineError):
            dawgie.context.fsm.updating_trigger()
        dawgie.context.fsm.starting_trigger()
        self.assertEqual('running', dawgie.context.fsm.state)

    def test_updating(self):
        dawgie.context.fsm = dawgie.pl.state.FSM(
            doctest_=True, initial_state='updating'
        )
        with self.assertRaises(MachineError):
            dawgie.context.fsm.contemplation_trigger()
        with self.assertRaises(MachineError):
            dawgie.context.fsm.gitting_trigger()
        with self.assertRaises(MachineError):
            dawgie.context.fsm.running_trigger()
        with self.assertRaises(MachineError):
            dawgie.context.fsm.starting_trigger()
        with self.assertRaises(MachineError):
            dawgie.context.fsm.update_trigger()
        with self.assertRaises(MachineError):
            dawgie.context.fsm.updating_trigger()
        dawgie.context.fsm.archiving_trigger()
        self.assertEqual('running', dawgie.context.fsm.state)
        dawgie.context.fsm = dawgie.pl.state.FSM(
            doctest_=True, initial_state='updating'
        )
        dawgie.context.fsm.loading_trigger()
        self.assertEqual('running', dawgie.context.fsm.state)
