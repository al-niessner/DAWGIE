'''schedule jobs based on DAG

Theory of operation is: given a DAG and a change event, determine which work can be done and in what order.

Definitions:
    DAG - directed graph normally built from source code as is done in Test/test_06
    change event - is identified by the 'run ID' and can be caused by:
        1. source code has changed
            a. git commit on main
            b. merge of a branch to main
        2. parent node has generated new data
        3. user has requested work be accomplished via command line or UI
    work - running of a 'dawgie.Algorithm', 'dawgie.Analyzer', or 'dawgie.Regression'.
    order - root of the DAG to its deepest leaf node. The level of the root is 0 and the deepest level is L. Available work at the lowest level should be done before work at higher levels.

Rules:
    1. Given two 'dawgie.Algorithm' nodes A and B with B is dependant on data produced by A, then B can begin processing a target as soon as A finishes.

    2. Given a 'dawgie.Algorithm' node A and a 'dawgie.Analyzer' node B where B is dependant on data produced by A, then B must wait for A to finish processing all targets before it can begin.

    3. Given a 'dawgie.Analyzer' node A and a 'dawgie.Algorithm' node B where B is dependant on data produced by A, then B can begin processing as soon as A finishes.

    4. Rule 1 is the same if either 'dawgie.Algorithm' node is replaced by 'dawgie.Regression'.

    5. Rules 2 and 3 are the same if 'dawgie.Algorithm' is replaced by 'dawgie.Regression'.

    6. Once a change event is detected, all subsequent changes are under the umbrella of the first change event (aka 'run ID').

Implementation:

The DAG is stored in a 'dawgie.pl.dag.Construct.at' where 'at' is specifically the algorithm tree (at) and it includes all work elements. Each node is of type 'xml.etree.ElementTree.Element' where the tag is the full name of the work element. The attributes of the node are used by the scheduler to maintain the scheduler queues. The attributes of the nodes are:
   {'feedback': {<Element 'feedback.model' at 0x7fb80ec79d50>},
    'shape': <Shape.ellipse: 0>,
    'visitors': {'feedback.sensor.measured.voltage'},
    'alg': <ae.feedback.bot.Sensor object at 0x7fb80e9e62f0>,
    'do': set(),
    'doing': set(),
    'factory': <function task at 0x7fb838aa6290>,
    'status': <State.initial: 5>,
    'todo': set(),
    'ancestry': set(),
    'been_here': True,
    'level': 0}

The important elements to the scheduler are do, doing, feedback, level, and todo. These allow the node to be added to 'per' and 'que' as necessary and keep track of what has been done and what has not. Processing a change event always starts by adding the information to the todo. When the event is processed with the DAG todo is completed, then the lowest level items are moved to do and doing - do is used by 'dawgie.farm' but setup in the scheduler.

Flow:

  organize() -> put targets into 'todo' and mark the 'state' 'waiting' if it is not running.
  next_job_batch() -> move 'todo' targets into 'doing' and 'do' for 'dawgie.pl.farm' where they are queued up for later processing and status changed to 'running'.
--

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

# pylint: disable=import-self

from dawgie.pl.jobinfo import State

import datetime
import dawgie
import dawgie.context
import dawgie.db
import dawgie.pl.dag
import dawgie.pl.promotion
import dawgie.pl.schedule
import dawgie.pl.version
import dawgie.util
import logging; log = logging.getLogger (__name__)
import twisted.internet.reactor

ae = None
booted = []
err = []
que = []
per = []
suc = []

pipeline_paused = False
promote = dawgie.pl.promotion.Engine()

class _DelayNotKnowableError(ArithmeticError): pass

def _delay (when:dawgie.EVENT)->datetime.timedelta:
    now = datetime.datetime.utcnow()
    today = now.isoweekday() - 1

    if when.moment.boot is not None:
        if when in booted: raise _DelayNotKnowableError()

        then = now
        booted.append (when)
    else:
        if when.moment.day is not None:
            then = datetime.datetime(year=when.moment.day.year,
                                     month=when.moment.day.month,
                                     day=when.moment.day.day,
                                     hour=when.moment.time.hour,
                                     minute=when.moment.time.minute,
                                     second=when.moment.time.second)
            pass

        if when.moment.dom is not None:
            nm = now.month + 1
            then = datetime.datetime(year=now.year + (1 if nm == 13 else 0),
                                     month=1 if nm == 13 else nm,
                                     day=when.moment.dom,
                                     hour=when.moment.time.hour,
                                     minute=when.moment.time.minute,
                                     second=when.moment.time.second)
            pass

        if when.moment.dow is not None:
            dd = datetime.timedelta (days=(7 + when.moment.dow - today)
                                     if when.moment.dow < today else
                                     (when.moment.dow-today))
            then = datetime.datetime (year=now.year,
                                      month=now.month,
                                      day=now.day,
                                      hour=when.moment.time.hour,
                                      minute=when.moment.time.minute,
                                      second=when.moment.time.second) + dd
            pass
        pass

    return then - now

def _diff (curr, prev):
    diff = []
    for k in curr:
        if k not in prev or prev[k].count (curr[k]) == 0: diff.append (k)
        pass
    return diff

def _is_asp (n:dawgie.pl.dag.Node)->bool:
    return n.get ('factory').__name__ == dawgie.Factories.analysis.name

def _priors (node):
    result = []
    if isinstance (node, dawgie.Algorithm): result = node.previous()
    if isinstance (node, dawgie.Analyzer): result = node.traits()
    if isinstance (node, dawgie.Regression): result = node.variables()
    return result

def _to_name (m):
    result = []
    for ak in m:
        for svk in m[ak].children:
            for vk in m[ak].children[svk].children:
                result.append ('.'.join ([ak, svk, vk]))
                pass
            pass
        pass
    return result

def algorithm_tree_view(): return dawgie.pl.schedule.ae.av

def build (factories, latest, previous):
    log.info ('build() - starting to build DAG')
    dawgie.pl.schedule.ae = dawgie.pl.dag.Construct(factories)
    promote.ae = dawgie.pl.schedule.ae
    promote.orgainize = dawgie.pl.schedule.organize
    dawgie.pl.schedule.que = []
    dawgie.pl.schedule.per = []
    log.info ('build() - computing version differences')
    dalg = _diff (latest[0], previous[1])
    dsv = _diff (latest[1], previous[2])
    dv = _diff (latest[2], previous[3])
    ans = {'.'.join (item.split ('.')[:2]) for item in dalg + dsv + dv}
    rev = dawgie.context.git_rev
    trglist = dawgie.db.targets()
    log.info ('build() - building schedule for new versions')
    for tn in ans:
        for t in dawgie.pl.schedule.ae.at:
            for n in t.locate (tn):\
                n.set ('todo',
                       set(['__all__']) if _is_asp (n) else set(trglist))
            pass
        pass
    log.info ('build() - calling organize with new versions')
    organize (ans, event=f'New software changeset {rev}')
    log.info ('build() - done building the schedule')
    return

def complete (job, runid, target, timing, status):
    history = err if status == State.failure else suc
    timing['completed'] = datetime.datetime.utcnow()
    timing = {k:str(v) for k,v in timing.items()}

    if target == '__all__': job.get ('doing').clear()
    elif target in job.get ('doing'): job.get ('doing').remove (target)

    if not (job.get ('todo') or job.get ('doing')):
        que.remove (job)
        job.set ('status', State.waiting)
        pass

    history.append ({'timing':timing,
                     'runid':runid,
                     'target':target,
                     'task':job.tag})
    return

def defer():
    if dawgie.pl.schedule.is_paused():
        twisted.internet.reactor.callLater (10, dawgie.pl.DeferWithLogOnError (defer, 'handling error while scheduling periodic event', __name__).callback, None)
        return

    delay = []
    for t in filter (lambda j:j.get ('status') not in [State.running,
                                                       State.waiting], per):
        t.set ('status', State.delayed)
        for p in t.get ('period'):
            try:
                ts = _delay (p).total_seconds()

                if ts <= 300.0:
                    que.append (t)
                    que.sort (key=lambda i:i.get ('level'))
                    t.set ('status', State.waiting)
                    t.set ('event', 'Periodic timer')

                    if _is_asp (t): t.get ('todo').add ('__all__')
                    else: t.get ('todo').update (dawgie.db.targets())

                    log.debug ('defer() - moving task %s to the job queue',
                               t.tag)
                else: delay.append (ts)
            except _DelayNotKnowableError:
                pass
            pass
        pass

    if delay:
        wait = min (delay)
        log.debug ('defer() - next wake up time in %s seconds',
                   str (round (wait)))
        twisted.internet.reactor.callLater (round (wait), dawgie.pl.DeferWithLogOnError (defer, 'handling error while scheduling periodic events', __name__).callback, None)
        pass
    return

def find (job)->dawgie.pl.dag.Node:
    jobid = job if isinstance (job, str) else job.tab
    avail = list(filter (lambda j:j.tag == jobid, que))
    return avail[0]

def is_paused(): return dawgie.pl.schedule.pipeline_paused

def next_job_batch():
    todo = []
    if not (promote() or dawgie.pl.schedule.is_paused()):
        jobs = {job.tag:job for job in que}
        for job in filter (lambda j:j.get ('todo'), que):
            available = job.get ('todo').copy()
            for dep in jobs.keys() & job.get ('ancestry'):
                for target in job.get ('todo'):
                    dependency = find (dep)

                    if target == '__all__' or \
                       '__all__'in dependency.get ('todo') or \
                       '__all__'in dependency.get ('doing'): available.clear()
                    if (target in dependency.get ('todo') or
                        target in dependency.get ('doing')) and \
                       target in available: available.remove (target)
                    pass
                pass
            for a in available: job.get ('todo').remove (a)
            job.get ('do').update (available)
            job.get ('doing').update (available)

            if available: todo.append (job)
            pass
        pass
    todo.sort (key=lambda j:j.get ('level'))
    return todo

def organize (task_names:[str], runid:int=None, targets:[str]=None,
              event:str=None):
    '''organize a schedule based on the calling event and what is already known

    Adds new targets to the todo list if it is not already there. If the job is
    already 'running' for a target, then keep the status as 'running'.
    '''
    jobs = {j.tag:j for j in que}
    targets = targets if targets else set()
    log.debug ('organize() - looping over targets')
    for tn in task_names:
        for t in dawgie.pl.schedule.ae.at:
            for n in t.locate (tn):
                jobs[n.tag] = n
                n.set ('runid', runid)
                n.set ('status', State.waiting if n.get ('status') is not State.running else State.running)

                if event: n.set ('event', event)
                if _is_asp (n): n.get ('todo').add ('__all__')
                elif '__all__' in targets:
                    n.get ('todo').update (dawgie.db.targets())
                else: n.get ('todo').update (targets)
                pass
            pass
        pass
    log.debug ('organize() - setting queue')
    dawgie.pl.schedule.que = sorted (jobs.values(),
                                     key=lambda i:i.get ('level'))
    return

def pause():
    dawgie.pl.schedule.pipeline_paused = True
    return

def periodics (factories):
    for p in factories:
        for event in p():
            an = '.'.join ([dawgie.util.task_name (event.algref.factory),
                            event.algref.impl.name()])
            for rta in dawgie.pl.schedule.ae.at:
                for n in rta.locate (an):
                    per.append (n)

                    if n.get ('period'): n.get ('period').append (event)
                    else: n.set ('period', [event])
                    pass
                pass
            pass
        pass
    defer()
    return

def purge (node:dawgie.pl.dag.Node, target:str):
    if target in node.get ('do',[]): node.get ('do').remove (target)
    if target in node.get ('doing',[]): node.get ('doing').remove (target)
    if target in node.get ('todo',[]): node.get ('todo').remove (target)

    for child in node: purge (child, target)
    return

def state_tree_view(): return dawgie.pl.schedule.ae.svv
def task_tree_view(): return dawgie.pl.schedule.ae.tv

def tasks():
    s = set()
    for r in dawgie.pl.schedule.ae.at:
        s.add (r.tag)
        for e in r.iter(): s.add (e.tag)
        pass
    return list(s)

def unpause(): dawgie.pl.schedule.pipeline_paused = False

def update (values:[(str,bool)], original:dawgie.pl.dag.Node, rid:int):
    log.debug ('update() - New values: %s', str(values))
    log.debug ('update() - Node name: %s', original.tag)
    log.debug ('update() - Run ID: %s', str(rid))

    if values:
        event = None
        feedbacks = dawgie.pl.schedule.ae.feedbacks
        targets = set()
        task_names = set()
        vns = set()
        for vn,_isnew in filter (lambda t:t[1], values):
            target = vn.split('.')[1]
            targets.add (target)
            fvn = '.'.join (vn.split('.')[2:])
            vns.add (fvn)

            if fvn in dawgie.pl.schedule.ae.feedbacks:
                event = 'following feedback loop'
                rid = None
                task_names.add ('.'.join (feedbacks[fvn].split ('.')[:2]))
                pass
            pass
        for node in filter (lambda n:n.tag != original.tag, original):
            for vref in dawgie.util.as_vref (_priors (node.get ('alg'))):
                if dawgie.util.vref_as_name (vref) in vns:\
                   task_names.add (node.tag)
                pass
            pass
        organize (sorted (task_names), rid, targets, event)
        if rid: promote (values, original, rid)
    else: log.error('Node %s for run ID %d did not update its state vector',
                    original.tag, rid)
    return

def view_doing() -> dict:
    active = list(filter (lambda t:t.get ('status') == State.running, que))
    return {a.tag:sorted (list(a.get ('doing'))) for a in active}

def view_events()->[{}]:
    result = {}
    for p in per:
        if p.tag not in result: result[p.tag] = set()

        for m in p.get ('period'):
            try: result[p.tag].add (round(_delay (m).total_seconds()))
            except _DelayNotKnowableError: result[p.tag].add (0)
            pass
        pass
    return [{'actor':k, 'delays':sorted(result[k])} for k in sorted (result)]

def view_failure() -> [dict]: return err
def view_success() -> [dict]: return suc

def view_todo() -> [dict]:
    wait = list(filter(lambda t:all([t.get ('status') in [State.waiting,
                                                          State.running],
                                     len(t.get ('todo'))]),  # prevents undefined
                       que))
    wait.sort (key=lambda t:t.get ('level'))
    return [{'name':w.tag,
             'targets':sorted (list(w.get ('todo')))} for w in wait]
