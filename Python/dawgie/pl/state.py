#!/usr/bin/env python3
'''The pipeline state machine

>>> fsm = FSM(doctest=True)
>>> fsm.starting_trigger()
self.start()
self._gui()
self._security()
self._logging()
self.load()
self._pipeline()
True
>>> fsm.state
'running'
>>> fsm.archiving_trigger()
self.archive()
self._archive_done()
True
>>> fsm.state
'running'
>>> fsm.update_trigger()
self.reload()
self._reload()
self.archive()
self._archive_done()
self.load()
self._pipeline()
True
>>> fsm.state
'running'
>>>

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

import builtins
import dawgie.context
import dawgie.db
import dawgie.fe
import dawgie.pl
import dawgie.pl.dag
import dawgie.pl.farm
import dawgie.pl.logger.fe
import dawgie.pl.resources
import dawgie.pl.scan
import dawgie.pl.schedule
import dawgie.pl.version
import dawgie.tools.submit
import dawgie.tools.trace
import doctest
import enum
import importlib
import logging; log = logging.getLogger(__name__)  # fmt: skip # noqa: E702 # pylint: disable=multiple-statements
import os
import pydot
import sys
import threading
import time
import transitions
import twisted.internet
import twisted.internet.ssl
import twisted.web.resource
import twisted.web.server


class RollbackImporter:
    # pylint: disable=redefined-builtin,too-few-public-methods,too-many-arguments,too-many-positional-arguments,too-many-public-methods
    def __init__(self):
        # Creates an instance and installs as the global importer
        self.dynamic_modules = set()
        self.real_import = builtins.__import__
        self.static_modules = sys.modules.copy()
        builtins.__import__ = self._import
        pass

    def _import(self, name, globals=None, locals=None, fromlist=(), level=0):
        result = self.real_import(name, globals, locals, fromlist, level)
        self.dynamic_modules.add(name)
        return result

    def reload(self):
        for modname in filter(
            lambda n: (
                n not in self.static_modules
                and n.startswith(dawgie.context.ae_base_package)
            ),
            self.dynamic_modules.copy(),
        ):
            if modname in sys.modules:
                importlib.reload(sys.modules[modname])
            pass
        return

    pass


class Status(enum.Enum):
    # enums should not scream at you so pylint: disable=invalid-name
    done = 0
    not_done = 1
    crashed = 2
    paused = 3
    pass


class FSM:
    # pylint: disable=too-many-instance-attributes,too-many-public-methods
    args = None
    states = [
        'archiving',
        'gitting',
        'loading',
        'running',
        'starting',
        'updating',
    ]

    def __init__(self, initial_state='starting', doctest_=False):
        self.machine = transitions.Machine(
            model=self, states=FSM.states, initial=initial_state
        )
        self.open_again = False
        self.changeset = None
        self.__doctest = doctest_
        self.dot_file_name = "state.dot"
        self.prior_state = initial_state
        self.inactive_color = "white"
        self.active_color = "green"
        self.time_machine = None
        self.__prior = None
        self.priority = None
        self.crew_thread = None
        self.doing_thread = None
        self.todo_thread = None
        self.wait_on_crew = threading.Event()
        self.wait_on_doing = threading.Event()
        self.wait_on_todo = threading.Event()
        self.reset()
        self.wait_timeout = 0.001
        self.nodes = {}
        self.graph = pydot.graph_from_dot_file(
            os.path.join(
                os.path.abspath(os.path.dirname(__file__)), self.dot_file_name
            )
        )
        idir = os.path.abspath(
            os.path.join(dawgie.context.fe_path, 'images/svg')
        )

        if not os.path.isdir(idir):
            os.makedirs(idir)

        fn = os.path.join(idir, 'state.svg')
        self.graph.write_svg(fn)
        for edge in self.graph.get_edges():
            self.machine.add_transition(
                **self.construct_attributes(edge.get_attributes())
            )
            pass
        for node in self.graph.get_nodes():
            node.set_style("filled")
            node.set_fillcolor(self.inactive_color)
            self.nodes[node.get_name()] = node
            pass
        return

    def _archive(self, *_args, **_kwds):
        log.info('entering state archive')
        basedir = os.path.abspath(
            os.path.join(dawgie.context.fe_path, 'pages/database')
        )
        os.makedirs(basedir, exist_ok=True)
        self.open_again = dawgie.db.reopen()
        # disable trace until issue 237 is addressed
        # dawgie.tools.trace.main (os.path.join(basedir, 'trace_report.html'),
        #                          dawgie.pl.schedule.ae.at)
        dawgie.db.close()
        dawgie.db.archive(self._archive_done)
        return

    def _archive_done(self):
        if self.__doctest:
            print('self._archive_done()')
        else:
            dawgie.pl.farm.archive = False

        if self.open_again:
            dawgie.db.open()

        self.open_again = False
        getattr(self, self.__prior + '_trigger')()
        return

    def _gui(self):
        if self.__doctest:
            print('self._gui()')
        else:
            factory = twisted.web.server.Site(dawgie.fe.root())

            if dawgie.security.use_tls():
                log.info('starting front end using HTTPS')
                cert = dawgie.security.authority()
                twisted.internet.reactor.listenSSL(
                    int(dawgie.context.fe_port), factory, cert.options()
                )
                if dawgie.security.clients():
                    twisted.internet.reactor.listenSSL(
                        dawgie.context.cfe_port,
                        factory,
                        cert.options(*dawgie.security.clients()),
                    )
            else:
                log.info('starting front end using HTTP')
                twisted.internet.reactor.listenTCP(
                    dawgie.context.fe_port, factory
                )
            pass
        return

    def _logging(self):
        if self.__doctest:
            print('self._logging()')
        else:
            dawgie.pl.logger.start(
                path=os.path.expanduser(
                    os.path.expandvars(
                        os.path.join(
                            dawgie.context.data_log, self.args.log_file
                        )
                    )
                ),
                port=dawgie.context.log_port,
            )
            dawgie.pl.logger.fe.instance = dawgie.pl.logger.fe.Handler()
            twisted_handler = dawgie.pl.logger.TwistedHandler(
                host=dawgie.context.db_host, port=dawgie.context.log_port
            )
            logging.basicConfig(
                handlers=[dawgie.pl.logger.fe.instance, twisted_handler],
                level=self.args.log_level,
            )
            logging.captureWarnings(True)
            pass
        return

    def _navel_gaze(self, *_args, **_kwds):
        log.info('entering state navel gaze')
        dawgie.pl.farm.insights = dawgie.pl.resources.distribution(
            dawgie.db.metrics()
        )
        log.info('exiting state navel gaze')
        return

    def _pipeline(self, *_args, **_kwds):
        # Begin the process of starting the pipeline
        if self.__doctest:
            print('self._pipeline()')
        else:
            facs = dawgie.pl.scan.for_factories(
                dawgie.context.ae_base_path, dawgie.context.ae_base_package
            )
            dawgie.db.open()
            dawgie.pl.schedule.build(
                facs,
                dawgie.pl.version.current(
                    facs[dawgie.Factories.analysis]
                    + facs[dawgie.Factories.regress]
                    + facs[dawgie.Factories.task]
                ),
                dawgie.pl.version.persistent(),
            )
            dawgie.pl.schedule.periodics(facs[dawgie.Factories.events])
            pass
        return

    def _reload(self, *args, **kwds):
        # pylint: disable=protected-access,unused-argument
        log.info('entering state updating (reload)')

        if self.__doctest:
            print('self._reload()')
        else:
            log.info("Jump into the time machine. Do the reload Rollback.")
            dawgie.db.close()
            dawgie.tools.submit.update_ops()
            dawgie.context.git_rev = dawgie.context._rev()
            self.time_machine.reload()
            pass

        log.info('exiting state updating (reload)')
        pass

    def _security(self):
        if self.__doctest:
            print('self._security()')
        else:
            dawgie.security.initialize(
                path=os.path.expandvars(
                    os.path.expanduser(dawgie.context.guest_public_keys)
                ),
                myname=dawgie.context.ssl_pem_myname,
                myself=os.path.expandvars(
                    os.path.expanduser(dawgie.context.ssl_pem_myself)
                ),
                system=dawgie.context.ssl_pem_file,
            )
        return

    def archive(self):
        if self.__doctest:
            print('self.archive()')
            self._archive_done()
        elif dawgie.pl.farm.archive:
            d = twisted.internet.threads.deferToThread(self._archive, 2)
            d.addErrback(
                dawgie.pl.LogFailure(
                    'while archiving the pipeline', __name__
                ).log
            )
        else:
            self._archive_done()
        return

    def construct_attributes(self, attributes):
        # Copy needed so that we don't overried the original
        d = attributes.copy()
        c = "conditions"

        if 'label' in d:
            del d['label']
        if c in d and isinstance(d[c], list):
            v = d[c][1:-1]
            v = v.split(" ")
            d[c] = list(v)
        return d

    def is_crew_done(self):
        # pylint: disable=protected-access
        while dawgie.pl.farm._busy and self.waiting_on_crew():
            time.sleep(0.2)
        return

    def is_doing_done(self):
        while dawgie.pl.schedule.view_doing() and self.waiting_on_doing():
            time.sleep(0.2)
        return

    def is_pipeline_active(self):
        return self.state == 'running'

    def is_todo_done(self):
        while dawgie.pl.schedule.que and self.waiting_on_todo():
            time.sleep(0.2)
        return

    def load(self):
        def done(*_args, **_kwds):
            self.running_trigger()

        log.info('entering state loading')

        if self.__doctest:
            print('self.load()')
            self._pipeline()
            done()
        else:
            log.info("Load the pipeline")
            dawgie.pl.farm.notify_all()
            dawgie.pl.farm.clear()
            d = twisted.internet.threads.deferToThread(self._pipeline, 2)
            d.addCallbacks(
                done,
                dawgie.pl.LogFailure(
                    'while loading the pipeline', __name__
                ).log,
            )
            pass

        log.info('exiting state loading')
        return

    def navel_gaze(self):
        d = twisted.internet.threads.deferToThread(self._navel_gaze, 2)
        d.addErrback(dawgie.pl.LogFailure('while navel gazing', __name__).log)
        return

    def reload(self):
        def done(*_args, **_kwds):
            self.archiving_trigger()

        if self.__doctest:
            print('self.reload()')
            self._reload()
            done()
        else:
            log.info('Reload the pipeline')
            d = twisted.internet.threads.deferToThread(self._reload, 2)
            d.addCallbacks(
                done,
                dawgie.pl.LogFailure(
                    'while reloading the pipeline', __name__
                ).log,
            )
            pass
        return

    def reset(self):
        self.wait_on_crew.set()
        self.wait_on_doing.set()
        self.wait_on_todo.set()
        self.priority = None
        return

    def save_prior_state(self):
        self.__prior = self.state
        return

    def set_submit_info(self, changeset, priority):
        try:
            priority = dawgie.tools.submit.Priority(priority)
        except:  # noqa: E722 # pylint: disable=bare-except
            log.error(
                'Could not convert "%s" to a meaningful priority defaulting to ToDo is empty',
                str(priority),
            )
            priority = dawgie.tools.submit.Priority.TODO
            pass
        self.priority = dawgie.tools.submit.Priority.max(
            self.priority, priority
        )
        self.changeset = changeset
        return

    def start(self):
        if self.__doctest:
            print('self.start()')

        log.info('entering state starting')
        self._security()
        self._gui()
        self._logging()
        log.info('Starting the pipeline')
        dawgie.pl.farm.plow()
        self.time_machine = RollbackImporter()
        log.info('exiting state starting')
        return

    def state_view(self):
        self.nodes[self.prior_state].set_fillcolor(self.inactive_color)
        self.prior_state = dawgie.context.fsm.state
        self.nodes[dawgie.context.fsm.state].set_fillcolor(self.active_color)
        return dawgie.pl.dag.Construct.graph(self.graph, [], 'current.svg')

    def submit_crossroads(self):
        # Check if we are in the correct state
        log.info("At the submit crossroads.")
        if not self.is_pipeline_active():
            log.warning(
                "Pipeline is not active while we are at the submit crossroad."
            )
        else:
            if self.priority is None:
                pass
            elif self.priority == dawgie.tools.submit.Priority.CREW:
                self.wait_for_crew()
            elif self.priority == dawgie.tools.submit.Priority.DOING:
                self.wait_for_doing()
            elif self.priority == dawgie.tools.submit.Priority.TODO:
                self.wait_for_todo()
            elif self.priority == dawgie.tools.submit.Priority.NOW:
                self.wait_for_nothing()
                pass
            pass
        return

    def wait_for_crew(self):
        def done(*_args, **_kwds):
            if self.waiting_on_crew():
                self.update_trigger()
                self.crew_thread = None
                pass
            return

        log.info("Waiting for crew to be empty.")
        self.wait_on_crew.clear()
        self.wait_on_doing.set()
        self.wait_on_todo.set()

        if self.crew_thread is None:
            self.crew_thread = twisted.internet.threads.deferToThread(
                self.is_crew_done
            )
            self.crew_thread.addCallbacks(
                done,
                dawgie.pl.LogFailure(
                    'while signaling crew is done', __name__
                ).log,
            )
            pass
        return

    def wait_for_doing(self):
        def done(*_args, **_kwds):
            if self.waiting_on_doing():
                self.update_trigger()
                self.doing_thread = None
                pass
            return

        log.info("Waiting for doing to be empty.")
        self.wait_on_doing.clear()
        self.wait_on_todo.set()

        if self.doing_thread is None:
            self.doing_thread = twisted.internet.threads.deferToThread(
                self.is_doing_done
            )
            self.doing_thread.addCallbacks(
                done,
                dawgie.pl.LogFailure(
                    'while signaling doing is done', __name__
                ).log,
            )
            pass
        return

    def wait_for_nothing(self):
        log.info("Not waiting for anything.")
        self.wait_on_todo.set()
        self.wait_on_doing.set()
        self.wait_on_crew.set()
        self.update_trigger()
        return

    def wait_for_todo(self):
        def done(*_args, **_kwds):
            if self.waiting_on_todo():
                self.update_trigger()
                self.todo_thread = None
                pass
            return

        log.info("Waiting for todo, doing, and crew to be empty.")
        self.wait_on_todo.clear()

        if self.todo_thread is None:
            self.todo_thread = twisted.internet.threads.deferToThread(
                self.is_todo_done
            )
            self.todo_thread.addCallbacks(
                done,
                dawgie.pl.LogFailure(
                    'while signaling todo is done', __name__
                ).log,
            )
            pass
        return

    def waiting_on_crew(self):
        return not self.wait_on_crew.wait(self.wait_timeout)

    def waiting_on_doing(self):
        return not self.wait_on_doing.wait(self.wait_timeout)

    def waiting_on_todo(self):
        return not self.wait_on_todo.wait(self.wait_timeout)

    pass


if __name__ == "__main__":
    doctest.testmod(verbose=True, exclude_empty=True)
    pass
