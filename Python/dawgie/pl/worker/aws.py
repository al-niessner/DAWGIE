'''

dawgie.context.cloud_data = "api-key@https_url@sqs-name@scale-name@cluster-name@task-name"

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

NTR: 49811
'''
import boto3
import base64
import datetime
import dawgie.db.util
import dawgie.context
import dawgie.pl.farm
import dawgie.pl.message
import dawgie.pl.worker
import importlib
import json
import logging
import os
import pickle
import requests
import tempfile
import twisted.internet.task

_contractors = []

# client or container side (no disk access)
class Context(dawgie.pl.worker.Context):
    def __init__(self, address:(str,int), revision:str, myid):
        dawgie.pl.worker.Context.__init__(self, address, revision)
        self.__cloud = dawgie.pl.message.Type.cloud
        self.__myid = myid
        return

    def decode (self, entry:str):
        return self._communicate (dawgie.pl.message.make
                                  (target=entry, typ=self.__cloud)).values

    def encode (self, value):
        return self._communicate (dawgie.pl.message.make
                                  (typ=self.__cloud, val=value)).values

    def move (self, fn:str, result:str):
        return self._communicate (dawgie.pl.message.make
                                  (rev=fn, target=result,
                                   typ=self.__cloud)).values

    def terminated (self):
        return self._communicate (dawgie.pl.message.make
                                  (jid=self.__myid, typ=self.__cloud))
    pass

# server side (has real disk access)
class Contractor(dawgie.pl.farm.Hand):
    def __init__(self, address):
        dawgie.pl.farm.Hand.__init__ (self, address)
        self.log = logging.getLogger(__name__)
        return

    def _process (self, msg):
        result = None

        if msg.type == dawgie.pl.message.Type.cloud:
            if msg.jobid:
                if msg.jobid in _contractors: _contractors.remove (msg.jobid)
                else: self.log.warning ('Job ID %s not found in my list of contractors %s',
                                        str(msg.jobid),
                                        str(list(sorted(_contractors))))
                self.transport.loseConnection()
            elif msg.revision and msg.target and not msg.values:
                result = dawgie.db.util.move (msg.revision, msg.target)
            elif not msg.revision and msg.target and not msg.values:
                result = dawgie.db.util.decode (msg.target)
            elif not msg.revision and not msg.target and msg.values:
                result = dawgie.db.util.encode (msg.values)
            else:
                self.log.error ('Unexpected message: %s', str(msg))
                self.transport.loseConnection()
                pass

            dawgie.pl.message.send (dawgie.pl.message.make
                                    (typ=dawgie.pl.message.Type.response,
                                     suc=result is not None, val=result), self)
        else: super()._process (msg)
        return

    def _reg (self, msg):
        # pylint: disable=protected-access
        if msg.revision != dawgie.context.git_rev:
            dawgie.pl.message.send (self._abort, self)
            self.log.warning ('Worker and pipeline revisions are not the same.')
            self.transport.loseConnection()
        else:
            dawgie.pl.farm._busy.append (msg.jobid + '[' +
                                         (msg.target if msg.target else
                                          '__all__') + ']')
            dawgie.pl.farm._time[dawgie.pl.farm._busy[-1]] = datetime.datetime.now()
            self.log.debug ('Registered a worker for its %d incarnation.',
                            msg.incarnation)
            pass
        return
    pass

class Company(twisted.internet.protocol.Factory):
    def buildProtocol (self, addr): return Contractor(addr)
    pass

class Connect:
    def __init__(self, job, respond, callLater=twisted.internet.reactor.callLater):
        self._callLater = callLater
        self._did = tempfile.mkdtemp()
        self._job = job
        self._kid = None
        self._log = logging.getLogger(__name__)
        self._pgp = dawgie.security.pgp()
        self._respond = respond
        os.rmdir (self._did)
        return

    def advertise (self):
        for k in self._pgp.list_keys():
            for u in k['uids']:
                if u.startswith ('dawgie-bot <'):
                    self._kid = k['keyid']
                    pass
                pass
            pass
        message = {'id':os.path.basename (self._did),
                   'now':datetime.datetime.utcnow(),
                   'payload':'',
                   'step':'advertise'}
        signed = self._pgp.sign (base64.b64encode (pickle.dumps (message)),
                                 keyid=self._kid, passphrase='1234567890')
        response = _https_push (signed.data)
        self._log.debug ('advertise: %s', response)

        if response != 'position posted': self._respond (self._job, False)
        else: self._callLater (0, dawgie.pl.DeferWithLogOnError (self.interview, 'while interviewing requester', __name__).callback, None)
        return

    def interview (self):
        message = {'id':os.path.basename (self._did),
                   'now':datetime.datetime.utcnow(),
                   'payload':'',
                   'step':'interview'}
        signed = self._pgp.sign (base64.b64encode (pickle.dumps (message)),
                                 keyid=self._kid, passphrase='1234567890')
        response = _https_push (signed.data)
        self._log.debug ('interview: %s', response)

        if response == 'False': self._respond (self._job, True)
        else:
            c,h,l,_i,s = json.loads (response)

            if c and h == 'Healthy' and l == 'InService' and s:
                self._callLater (0, dawgie.pl.DeferWithLogOnError(self.hire, 'while hiring requestor', __name__).callback, None)
            else: self._callLater (15, dawgie.pl.DeferWithLogOnError(self.interview, 'while interviewing requester', __name__).callback, None)
        pass
        return

    def hire (self):
        message = {'id':os.path.basename (self._did),
                   'now':datetime.datetime.utcnow(),
                   'payload':dawgie.pl.message.dumps (self._job),
                   'step':'hire'}
        signed = self._pgp.sign (base64.b64encode (pickle.dumps (message)),
                                 keyid=self._kid, passphrase='1234567890')
        response = _https_push (signed.data)
        self._log.debug ('hired')

        if response and response not in [b'False', 'False']:\
           started = self._pgp.verify (response).valid
        if started: _contractors.append (self._did)
        else:
            self._log.warning ('Failed to hire an AWS contractor')
            self._respond (self._job, False)
            pass
        return
    pass

def _advertise():
    asg = boto3.client ('autoscaling')
    sn = dawgie.context.cloud_data.split ('@')[3]
    asg.set_desired_capacity (AutoScalingGroupName=sn, DesiredCapacity=1)
    return 'position posted'

def _interview():
    asg = boto3.client ('autoscaling')
    ecs = boto3.client ('ecs')
    sn,cn = dawgie.context.cloud_data.split ('@')[3:5]
    g = asg.describe_auto_scaling_groups (AutoScalingGroupNames=[sn])
    c,h,l,iid,cs = 0,'none','none','',False

    if g['AutoScalingGroups'][0]['Instances']:
        c = len (g['AutoScalingGroups'][0]['Instances'])
        h = g['AutoScalingGroups'][0]['Instances'][0]['HealthStatus']
        l = g['AutoScalingGroups'][0]['Instances'][0]['LifecycleState']
        iid = g['AutoScalingGroups'][0]['Instances'][0]['InstanceId']
        r = {'nextToken':''}
        while 'nextToken' in r and not cs:
            nt = r['nextToken']
            r = ecs.list_container_instances (cluster=cn, nextToken=nt)
            if r['containerInstanceArns']:
                cids = [carn.split('/')[-1]
                        for carn in r['containerInstanceArns']]
                dci = ecs.describe_container_instances (cluster=cn,
                                                        containerInstances=cids)
                for ci in dci['containerInstances']:\
                    cs |= ci['ec2InstanceId'] == iid and ci['agentConnected']
                pass
            pass
        pass
    return c,h,l,iid,cs

def _hire (iid):
    asg = boto3.client ('autoscaling')
    ecs = boto3.client ('ecs')
    sn,cn,td = dawgie.context.cloud_data.split ('@')[3:]
    asg.detach_instances (InstanceIds=[iid],
                          AutoScalingGroupName=sn,
                          ShouldDecrementDesiredCapacity=True)
    r = ecs.run_task (cluster=cn, count=1, taskDefinition=td,
                      placementConstraints=[{'type':'distinctInstance'}])
    for f in r['failures']: print ('_awake() - failure -', f)

    if r['failures']: raise ValueError('Did not activate a cluster request')
    return

def _https_push (msg):
    log = logging.getLogger (__name__)
    api_key,url = dawgie.context.cloud_data.split ('@')[0:2]
    response = requests.post (url,
                              json={'request':msg.decode()},
                              headers={'x-api-key':api_key})

    if response.status_code != 200:\
       log.error ('failed to communicate with AWS successfully (status code, message): (%d, %s)', response.status_code, response.text)
    return response.text if response.status_code == 200 else 'False'

def _sqs_pop():
    name = dawgie.context.cloud_data.split ('@')[2]
    resource = boto3.resource ('sqs')
    sqs = resource.get_queue_by_name (QueueName=name)
    message = []
    while not message:
        message = sqs.receive_messages (MaxNumberOfMessages=1)

        if message and message[0].body:
            msg = message[0].body
            message[0].delete()
        else: message = []
        pass
    return json.loads (msg)

def _sqs_push (msg):
    name = dawgie.context.cloud_data.split ('@')[2]
    resource = boto3.resource ('sqs')
    sqs = resource.get_queue_by_name (QueueName=name)
    sqs.send_message (MessageBody=json.dumps (msg), MessageGroupId='request')
    return

def do (job, respond):
    twisted.internet.reactor.callLater (0, dawgie.pl.DeferWithLogOnError (Connect (job, respond).advertise, 'while advertising AWS service', __name__).callback, None)
    return

def exchange (message):  # AWS lambda function
    _pgp = dawgie.security.pgp()
    response = 'False'
    print ('exchange() - start')
    # pylint: disable=broad-except,too-many-nested-blocks,undefined-variable
    try:
        if _pgp.verify (message):
            print ('exchange() - verified')
            message = pickle.loads (base64.b64decode
                                    (_pgp.decrypt (message).data[:-1]))
            mid = message['id']
            step = message['step']

            if (datetime.datetime.utcnow()-message['now']).total_seconds() < 50:
                print ('exchange() - within time bounds')
                print ('exchange() - do', step)
                if step == 'advertise': response = _advertise()
                if step == 'interview': response = json.dumps (_interview())
                if step == 'hire':
                    payload = base64.b64encode (message['payload']).decode()
                    for k in _pgp.list_keys():
                        for u in k['uids']:
                            if u.startswith ('aws-bot <'): keys = k
                            pass
                        pass
                    pk = _pgp.export_keys ([keys['fingerprint']])
                    sk = _pgp.export_keys ([keys['fingerprint']], secret=True,
                                           passphrase='1234567890')
                    # Sign.data dynamic so pylint: disable=no-member
                    signed = _pgp.sign (pk, keyid=keys['fingerprint'],
                                        passphrase='1234567890').data
                    # pylint: enable=no-member
                    print ('exchange() - get IID')
                    iid = _interview()[3]
                    print ('exchange() - push to SQS')
                    _sqs_push ({'id':mid, 'iid':iid, 'payload':payload,
                                'pubkey':pk, 'seckey':sk})
                    print ('exchange() - hire task in ECS')
                    _hire (iid)
                    response = signed.decode()
                    pass
            else: print ('exchange() - invalid timestamp')
        else: print ('exchange() - invalid signature')
    except Exception: log.exception('Exception processing request')
    print ('exchange() - complete')
    return response

def execute (address:(str,int), inc:int, ps_hint:int, rev:str):
    # pylint: disable=too-many-statements
    log = None
    iid,myid,job = sqs_pop()
    try:
        s = dawgie.security.connect (address)
        m = job._replace (type=dawgie.pl.message.Type.register,
                          incarnation=inc,
                          revision=rev)
        dawgie.pl.message.send (m, s)
        s.close()
        ctxt = Context(address, rev, myid)
        dawgie.db.util.decode = ctxt.decode
        dawgie.db.util.encode = ctxt.encode
        dawgie.db.util.move = ctxt.move

        if job.type == dawgie.pl.message.Type.cloud:
            # pylint: disable=bare-except
            if job.ps_hint is not None: ps_hint = job.ps_hint

            dawgie.context.loads (job.context)
            dawgie.db.reopen()
            handler = dawgie.pl.logger.TwistedHandler\
                      (host=address[0], port=dawgie.context.log_port)
            handler.setLevel (dawgie.context.log_level)
            logging.basicConfig (handlers=[handler, logging.StreamHandler()],
                                 level=dawgie.context.log_level)
            logging.captureWarnings (True)
            log = logging.getLogger (__name__)
            log.critical ('starting AWS work')
            try:
                factory = getattr (importlib.import_module (job.factory[0]),
                                   job.factory[1])
                nv = ctxt.run (factory, ps_hint,
                               job.jobid, job.runid, job.target, job.timing)
                m = dawgie.pl.message.make (typ=dawgie.pl.message.Type.response,
                                            inc=job.target,
                                            jid=job.jobid,
                                            rid=job.runid,
                                            suc=True,
                                            tim=job.timing,
                                            val=nv)
            except (dawgie.NoValidInputDataError,dawgie.NoValidOutputDataError):
                logging.getLogger(__name__).exception ('Job "%s" had invalid data for run id %s and target "%s"',  str(m.jobid), str(m.runid), str(m.target))
                m = dawgie.pl.message.make (typ=dawgie.pl.message.Type.response,
                                            inc=m.target,
                                            jid=m.jobid,
                                            rid=m.runid,
                                            suc=None,
                                            tim=m.timing)
            except:
                logging.getLogger(__name__).exception ('Job "%s" failed to execute successfully for run id %s and target "%s"', str (job.jobid), str (job.runid), str (job.target))
                m = dawgie.pl.message.make (typ=dawgie.pl.message.Type.response,
                                            inc=job.target,
                                            jid=job.jobid,
                                            rid=job.runid,
                                            suc=False,
                                            tim=job.timing)
            finally:
                dawgie.db.close()

                if not ctxt.abort():
                    s = dawgie.security.connect (address)
                    dawgie.pl.message.send (m, s)
                    s.close()
                    pass

                ctxt.terminated()
                pass
        else: raise ValueError('Wrong message type: ' + str (job.type))
    finally:
        if log: log.critical ('terminating self')
        ec2 = boto3.client ('ec2')
        ec2.terminate_instances (InstanceIds=[iid], DryRun=False)
        pass
    return

def initialize():
    twisted.internet.reactor.listenTCP (int(dawgie.context.cloud_port),
                                        Company(),
                                        dawgie.context.worker_backlog)
    return

def sqs_pop():
    message = _sqs_pop()
    dawgie.security.extend ([message['pubkey'], message['seckey']])
    job = dawgie.pl.message.loads (base64.b64decode (message['payload']))
    return message['iid'],message['id'],job
