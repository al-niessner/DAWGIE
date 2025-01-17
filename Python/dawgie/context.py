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

import argparse
import enum
import dawgie.types
import importlib
import inspect
import logging
import os
import pickle
import subprocess

# All of the names in this file are meant to mean more than a global variable
# so ignoring all of the naming rules, pylint: disable=invalid-name


class CloudProvider(enum.Enum):
    aws = 0
    none = 1
    pass


class PortOffset(enum.Enum):
    certFE = 5
    cloud = 4
    farm = 1
    frontend = 0
    log = 2
    shelve = 3
    pass


ae_base_path = os.environ.get('DAWGIE_AE_BASE_PATH', '/proj/src/ae')
ae_base_package = os.environ.get('DAWGIE_AE_BASE_PACKAGE', 'ae')

allow_promotion = os.environ.get('DAWGIE_PROMOTION', 'false').lower() in 'true'

cfe_port = int(
    os.environ.get('DAWGIE_CFE_PORT', 8080 + PortOffset.certFE.value)
)
cloud_data = os.environ.get(
    'DAWGIE_CLOUD_DATA',
    'apikey@url@SQS_Name@AutoScalingGroupName@ClusterName@TaskDefinition',
)
cloud_port = int(
    os.environ.get('DAWGIE_CLOUD_PORT', 8080 + PortOffset.cloud.value)
)
cloud_provider = CloudProvider.none

cpu_threshold = int(os.environ.get('DAWGIE_CPU_THRESH', 30))

data_dbs = os.environ.get('DAWGIE_DATA_DBSTOR', '/proj/data/dbs')
data_log = os.environ.get('DAWGIE_DATA_LOGDIR', '/proj/data/logs')
data_stg = os.environ.get('DAWGIE_DATA_STAGED', '/proj/data/stg')

db_host = os.environ.get('DAWGIE_DB_HOST', 'localhost')
db_impl = os.environ.get('DAWGIE_DB_IMPL', 'shelve')
db_name = os.environ.get('DAWGIE_DB_NAME', 'undefined')
db_path = os.environ.get('DAWGIE_DB_PATH', '/proj/data/db')
db_post2shelve_prefix = os.environ.get(
    'DAWGIE_DB_POST2SHELVE_PREFIX', 'undefined'
)
db_rotate_path = os.environ.get('DAWGIE_DB_ROTATE_PATH', '/proj/data/db')
db_copy_path = os.environ.get('DAWGIE_DB_COPY_PATH', '/tmp')
db_port = int(os.environ.get('DAWGIE_DB_PORT', 8080 + PortOffset.shelve.value))
db_rotate = os.environ.get('DAWGIE_DB_ROTATES', 10)
db_lock = False

display = os.environ.get('DAWGIE_DISPLAY_TYPE', 'html')
email_alerts_to = os.environ.get('DAWGIE_EMAIL_ALERTS_TO', '')
email_signature = dawgie.resolve_username()
farm_port = int(
    os.environ.get('DAWGIE_FARM_PORT', 8080 + PortOffset.farm.value)
)
fe_path = os.environ.get(
    'DAWGIE_FE_PATH', '/tmp/' + os.environ.get('USERNAME', 'unknown') + '/fe'
)
fe_port = int(
    os.environ.get('DAWGIE_FE_PORT', 8080 + PortOffset.frontend.value)
)
git_rev = None
guest_public_keys = os.environ.get(
    'DAWGIE_GUEST_PUBLIC_KEYS', '/proj/data/certs'
)
identity_override = os.environ.get(
    'DAWGIE_SECURITY_FETCH_IDENTITY', 'dawgie.security.fetch_identity'
)
log_backup = 10
log_capacity = 100
log_level = logging.WARN
log_port = int(os.environ.get('DAWGIE_LOG_PORT', 8080 + PortOffset.log.value))
sanction_override = os.environ.get(
    'DAWGIE_SECURITY_IS_SANCTIONED', 'dawgie.security.is_sanctioned'
)
ssl_pem_file = os.environ.get('DAWGIE_SSL_PEM_FILE', '')
ssl_pem_myname = os.environ.get('DAWGIE_SSL_PEM_MYNAME', 'dawgie')
ssl_pem_myself = os.environ.get('DAWGIE_SSL_PEM_MYSELF', '')
worker_backlog = 50


def _rev():
    rev = os.environ.get('DAWGIE_DOCKERIZED_AE_GIT_REVISION', '')

    if not rev:
        cdir = os.path.abspath(os.curdir)
        os.chdir(os.path.abspath(ae_base_path))
        rev = (
            subprocess.check_output(['git', 'rev-parse', 'HEAD'])
            .decode()
            .strip()
        )
        os.chdir(cdir)
        pass
    return rev


def add_arguments(ap):
    '''Add arguments to override the environment from the command line

    ap - an instance of argparse.ArgumentParser that is being used
    '''
    ap.add_argument(
        '--context',
        default=None,
        required=False,
        help='a Python dictionary to load into context first',
    )
    ap.add_argument(
        '--context-ae-dir',
        default=ae_base_path,
        required=False,
        help='the complete path to the AE directory [%(default)s]',
    )
    ap.add_argument(
        '--context-ae-pkg',
        default=ae_base_package,
        required=False,
        help='the package prefix for the AE [%(default)s]',
    )
    ap.add_argument(
        '--context-allow-promotion',
        action='store_true',
        required=False,
        help='allow the dawgie to promote state vectors',
    )
    ap.add_argument(
        '--context-cloud-data',
        default=cloud_data,
        required=False,
        help='data used to communicate with the cloud provider',
    )
    ap.add_argument(
        '--context-cfe-port',
        default=cfe_port,
        required=False,
        type=int,
        help='the port to the client certified frontend [%(default)s]',
    )
    ap.add_argument(
        '--context-cloud-port',
        default=cloud_port,
        required=False,
        type=int,
        help='the port to the cloud foreman [%(default)s]',
    )
    ap.add_argument(
        '--context-cloud-provider',
        choices=[cp.name for cp in CloudProvider],
        default=CloudProvider.none.name,
        required=False,
        help='which cloud provider to use [%(default)s]',
    )
    ap.add_argument(
        '--context-cpu-threshold',
        default=cpu_threshold,
        required=False,
        type=int,
        help='the number of seconds of compute time to be cloud worthy [%(default)s]',
    )
    ap.add_argument(
        '--context-data-dbs',
        default=data_dbs,
        required=False,
        help='location of the DB data store [%(default)s]',
    )
    ap.add_argument(
        '--context-data-log',
        default=data_log,
        required=False,
        help='location of the log files [%(default)s]',
    )
    ap.add_argument(
        '--context-data-stg',
        default=data_stg,
        required=False,
        help='location of the staging store [%(default)s]',
    )
    ap.add_argument(
        '--context-db-copy-path',
        default=db_copy_path,
        required=False,
        help='where to copy the database [%(default)s]',
    )
    ap.add_argument(
        '--context-db-host',
        default=db_host,
        required=False,
        help='the host of the database [%(default)s]',
    )
    ap.add_argument(
        '--context-db-impl',
        default=db_impl,
        required=False,
        help='ehich database implementation to use [%(default)s]',
    )
    ap.add_argument(
        '--context-db-name',
        default=db_name,
        required=False,
        help='the name of the database [%(default)s]',
    )
    ap.add_argument(
        '--context-db-path',
        default=db_path,
        required=False,
        help='where to find the database [%(default)s]',
    )
    ap.add_argument(
        '--context-db-port',
        default=db_port,
        required=False,
        type=int,
        help='the port to the database [%(default)s]',
    )
    ap.add_argument(
        '--context-db-rotate',
        default=db_rotate,
        required=False,
        type=db_rotate_type,
        help='the max number of data rotations allowed [%(default)s]',
    )
    ap.add_argument(
        '--context-db-rotate-path',
        default=db_rotate_path,
        required=False,
        help='the path of where the rotated db will be located [%(default)s]',
    )
    ap.add_argument(
        '--context-display-type',
        choices=[d.name for d in dawgie.types.DisplayType],
        default='html',
        required=False,
        help='what type of display [%(default)s]',
    )
    ap.add_argument(
        '--context-farm-port',
        default=farm_port,
        required=False,
        type=int,
        help='the port to the farm foreman [%(default)s]',
    )
    ap.add_argument(
        '--context-fe-path',
        default=fe_path,
        required=False,
        type=str,
        help='AE specific directory for the front-end [%(default)s]',
    )
    ap.add_argument(
        '--context-guest-public-keys',
        default=guest_public_keys,
        required=False,
        help='location to find the public keys for all guests [%(default)s]',
    )
    ap.add_argument(
        '--context-log-backup',
        default=log_backup,
        required=False,
        type=int,
        help='the number of log files to accumulate in the log directory [%(default)s]',
    )
    ap.add_argument(
        '--context-log-capacity',
        default=log_capacity,
        required=False,
        type=int,
        help='the number of log messages to save for the front-end lists [%(default)s]',
    )
    ap.add_argument(
        '--context-log-port',
        default=log_port,
        required=False,
        type=int,
        help='the port to the log server [%(default)s]',
    )
    ap.add_argument(
        '--context-email-alerts-to',
        default=email_alerts_to,
        required=False,
        help='email address(es) to send alerts to using a , to separate them when more than one. [%(default)s]',
    )
    ap.add_argument(
        '--context-email-signature',
        default=email_signature,
        required=False,
        help='Sign e-mail summary reports with this signature. [%(default)s]',
    )
    ap.add_argument(
        '--context-security-fetch-identity',
        default=identity_override,
        required=False,
        help='fetch a meaningful identity from the client certificate [%(default)s]',
    )
    ap.add_argument(
        '--context-security-is-sanctioned',
        default=sanction_override,
        required=False,
        help='determine if a client has access to the endpoint [%(default)s]',
    )
    ap.add_argument(
        '--context-ssl-pem-file',
        default=ssl_pem_file,
        required=False,
        help='when pointing at an existing file, it will be used to initiate an https service [%(default)s]',
    )
    ap.add_argument(
        '--context-ssl-pem-myname',
        default=ssl_pem_myname,
        required=False,
        help='host name for the "myself" certificate [%(default)s]',
    )
    ap.add_argument(
        '--context-ssl-pem-myself',
        default=ssl_pem_myself,
        required=False,
        help='a private SSL/TLS key and cert to be used for internal communications [%(default)s]',
    )
    ap.add_argument(
        '--context-worker-backlog',
        default=worker_backlog,
        required=False,
        type=int,
        help='the number of expected workers that may try to contact the foreman at the same time [%(default)s]',
    )
    return


def dumps() -> bytes:
    def isattribute(member):
        return not (
            (member[0].startswith('__') and member[0].endswith('__'))
            or inspect.isbuiltin(member[1])
            or inspect.isfunction(member[1])
            or inspect.ismodule(member[1])
            or inspect.isroutine(member[1])
            # avoid cicular dependencies by checking the string of the type
            or str(type(member[1])) == "<class 'dawgie.pl.state.FSM'>"
        )

    attributes = list(filter(isattribute, inspect.getmembers(dawgie.context)))
    return pickle.dumps(attributes, pickle.HIGHEST_PROTOCOL)


def loads(b: bytes) -> None:
    attributes = pickle.loads(b)
    for a in attributes:
        setattr(dawgie.context, *a)
    return


def lock_db():
    dawgie.context.db_lock = True
    return


def db_rotate_type(x):
    x = int(x)
    if x < 1:
        raise argparse.ArgumentTypeError("Minimum db_rotate is 1")
    return x


def override(args):
    '''Use the command line inputs to override the environment

    args - the result of ap.parse_args() {see add_arguments() in this module}
    '''
    # pylint: disable=too-many-statements
    if args.context:
        mod_name = '.'.join(args.context.split('.')[:-1])
        var_name = args.context.split('.')[-1]
        mod = importlib.import_module(mod_name)
        dawgie.context.__dict__.update(getattr(mod, var_name))
        pass

    if args.context_db_impl == 'post':
        if args.context_db_port == fe_port + PortOffset.shelve.value:
            args.context_db_port = 5432
            pass
        if args.context_db_path.find(':') < 0:
            args.context_db_path = 'username:password'
            pass
        pass

    if args.context_db_impl == 'shelve':
        # This db_path is the value before it is overriden
        if args.context_db_rotate_path == db_path:
            args.context_db_rotate_path = args.context_db_path
            pass
        pass

    dawgie.context.ae_base_path = args.context_ae_dir
    dawgie.context.ae_base_package = args.context_ae_pkg
    dawgie.context.allow_promotion = args.context_allow_promotion
    dawgie.context.cfe_port = args.context_cfe_port
    dawgie.context.cloud_data = args.context_cloud_data
    dawgie.context.cloud_port = args.context_cloud_port
    dawgie.context.cloud_provider = CloudProvider[args.context_cloud_provider]
    dawgie.context.cpu_threshold = args.context_cpu_threshold
    dawgie.context.data_dbs = args.context_data_dbs
    dawgie.context.data_log = args.context_data_log
    dawgie.context.data_stg = args.context_data_stg
    dawgie.context.db_copy_path = args.context_db_copy_path
    dawgie.context.db_host = args.context_db_host
    dawgie.context.db_impl = args.context_db_impl
    dawgie.context.db_name = args.context_db_name
    dawgie.context.db_path = args.context_db_path
    dawgie.context.db_port = args.context_db_port
    dawgie.context.db_rotate = args.context_db_rotate
    dawgie.context.db_rotate_path = args.context_db_rotate_path
    dawgie.context.display = dawgie.types.DisplayType[args.context_display_type]
    dawgie.context.email_alerts_to = args.context_email_alerts_to
    dawgie.context.email_signature = args.context_email_signature
    dawgie.context.farm_port = args.context_farm_port
    dawgie.context.fe_path = args.context_fe_path
    dawgie.context.git_rev = _rev()
    dawgie.context.guest_public_keys = args.context_guest_public_keys
    dawgie.context.identity_override = args.context_security_fetch_identity
    dawgie.context.log_backup = args.context_log_backup
    dawgie.context.log_capacity = args.context_log_capacity
    dawgie.context.log_port = args.context_log_port
    dawgie.context.sanction_override = args.context_security_is_sanctioned
    dawgie.context.ssl_pem_file = args.context_ssl_pem_file
    dawgie.context.ssl_pem_myname = args.context_ssl_pem_myname
    dawgie.context.ssl_pem_myself = args.context_ssl_pem_myself
    dawgie.context.worker_backlog = args.context_worker_backlog

    if not dawgie.context.ae_base_path.endswith(
        os.path.sep + dawgie.context.ae_base_package.replace('.', os.path.sep)
    ):
        raise ValueError(
            f'context-ae-dir ({0}) does not end with context-ae-pkg ({dawgie.context.ae_base_path}, {dawgie.context.ae_base_package})'
        )
    return


def unlock_db():
    dawgie.context.db_lock = False
    return
