#! /usr/bin/env python3
'''Merge changeset into pre_ops

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

# pylint: disable=import-self

import argparse
import email.mime.text
import enum
import git
import logging
import smtplib
import subprocess


class Priority(enum.Enum):
    NOW = "now"
    CREW = "crew_idle"
    DOING = "doing_empty"
    TODO = "todo_empty"

    @staticmethod
    def max(*largs):
        result = Priority.TODO
        for a in filter(lambda a: a is not None, largs):
            if a == Priority.NOW:
                result = a
            if a == Priority.CREW and result != Priority.NOW:
                result = a
            if (
                a == Priority.DOING
                and result != Priority.CREW
                and result != Priority.NOW
            ):
                result = a
            pass
        return result

    pass


class State(enum.IntEnum):
    FAILED = 1
    SUCCESS = 2
    pass


# pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-return-statements
def automatic(changeset, loc, ops, repo, stable, test, spawn):
    '''fully automatic processing to update the main branch

    0. get all the remote changes
    1. switch to a testing branch from stable branch
    2. pull the stable branch into the testing branch
    3. verify dawgie.tools.compliant ABD changeset matches
      if compliant:
        b. delete ops branch
        c. branch stable to ops at the changeset
    4. checkout ops branch
    5. delete test branch

    changeset: the git changeset to move to
    ops: the branch considered operational
    repo: the path to the top of the repository
    stable: the branch to pull the changeset from
    test: the name of a temporary branch for compliance testing
    '''
    g = git.cmd.Git(repo)
    status = State.FAILED
    try:
        status = git_execute(g, f'git checkout {stable}')
        if status == State.FAILED:
            return status
        status = git_execute(g, f'git pull {loc} {stable}')
        if status == State.FAILED:
            return status
        status = git_execute(g, f'git rebase {stable} {test}')
        if status == State.FAILED:
            return status
        cs = g.execute('git rev-parse HEAD'.split())
        if cs != changeset:
            mail_out(
                f'The current HEAD of {stable} is {cs} while you are asking for {changeset}. Aborting the automatic merging of {stable} to {ops}'
            )
            return State.FAILED
        status = auto_merge_compliant(changeset, repo, spawn)
        if status == State.FAILED:
            return status
        status = git_execute(g, f'git checkout {stable}')
        if status == State.FAILED:
            return status
        status = git_execute(g, f'git rebase {stable} {ops}')
        if status == State.FAILED:
            return status
    finally:
        git_execute(g, f'git checkout {ops}')
        if status == State.SUCCESS:
            mail_out(f'The operational AE is now at {changeset}.')
        else:
            mail_out(
                f'Failed to update the operational AE to {changeset}. '
                'Check the state of the pipeline before continuing.'
            )
    return State.SUCCESS


# pylint: enable=too-many-arguments,too-many-positional-arguments,too-many-return-statements


def _spawn(cmd: [str]):
    return subprocess.call(cmd) == 0


def already_applied(changeset, a_repo_dir):
    g = git.cmd.Git(a_repo_dir)
    gl = g.execute('git log'.split())
    return -1 < gl.find(changeset)


def auto_merge_compliant(changeset, repo, spawn):
    # Validate compliance
    # run compliance
    # if failed then revert git reset --hard ORIG_HEAD
    # otherwise continue
    if not dawgie.tools.compliant.verify(repo, True, False, spawn):
        msg = (
            f"Compliancy check failed. Please run compliant.py for {changeset}"
        )
        mail_out(msg)
        return State.FAILED
    return State.SUCCESS


def git_execute_d(func):
    def func_wrapper(g, cmd):
        status = State.FAILED
        try:
            status = func(g, cmd)
        except git.exc.GitCommandError as e:
            logging.error(e)
            status = State.FAILED
        return status

    return func_wrapper


@git_execute_d
def git_execute(g, cmd):
    g.execute(cmd.split(' '))
    return State.SUCCESS


def mail_out(msg):
    if dawgie.context.email_alerts_to:
        message = email.mime.text.MIMEText(msg)
        message['Subject'] = "DAWGIE Submit results"
        message["From"] = (
            "no-reply"
            + dawgie.context.email_alerts_to.split(',')[0].split('@')[1]
        )
        message["To"] = dawgie.context.email_alerts_to
        try:
            s = smtplib.SMTP("localhost")
            s.send_message(message)
            s.quit()
            logging.critical('Sent email alert with: %s', str(msg))
        except OSError:
            logging.critical('No email: %s', str(msg))
    else:
        logging.info(msg)
    return


def merge_into(g, loc, src, dst):
    status = git_execute(g, f"git merge {loc}/{src}")
    if status == State.FAILED:
        msg = f"Failed to merge {src} into {dst}."

        if git_execute(g, "git merge --abort") == State.FAILED:
            msg += "\nFailed to abort merge. Take Action! Take Action!"
        mail_out(msg)
        pass
    return status


if __name__ == "__main__":
    import dawgie.context
    import dawgie.tools.compliant
    import dawgie.tools.submit
    import dawgie.util

    ap = argparse.ArgumentParser(
        description='Merge the CHANGE_SET into PRE_OPS. Verify that it is dawgie.tools.compliant. If it is compliant, merge it in OPS.'
    )
    ap.add_argument(
        '-l',
        '--log-file',
        default=None,
        required=False,
        help='a filename to put all of the log messages into [%(default)s]',
    )
    ap.add_argument(
        '-L',
        '--log-level',
        default=logging.ERROR,
        required=False,
        type=dawgie.util.log_level,
        help='set the verbosity that you want where a smaller number means more verbose [logging.INFO]',
    )
    ap.add_argument(
        '-c',
        '--changeset',
        default=None,
        required=True,
        help='The changeset to verify then merge to the final/stable/operational branch.',
    )
    ap.add_argument(
        '-r',
        '--repository-dir',
        required=True,
        help='set repo directory where you want to do the merging',
    )
    ap.add_argument(
        '-R',
        '--remote',
        default=dawgie.context.ae_repository_remote,
        required=False,
        help='The name of the remoate location for the stable branch [%(default)s].',
    )
    ap.add_argument(
        '-o',
        '--branch-operational',
        default=dawgie.context.ae_repository_branch_ops,
        required=False,
        help='The name of the final or stable or operational branch [%(default)s].',
    )
    ap.add_argument(
        '-s',
        '--branch-stable',
        default=dawgie.context.ae_repository_branch_stable,
        required=False,
        help='The name of the final or stable or operational branch [%(default)s].',
    )
    ap.add_argument(
        '-t',
        '--branch-test',
        default=dawgie.context.ae_repository_branch_test,
        required=False,
        help='The name of the branch for testing the new commit to verify it is dawgie.tools.compliant  [%(default)s]',
    )
    dawgie.context.add_arguments(ap)
    args = ap.parse_args()
    dawgie.context.override(args)
    logging.basicConfig(filename=args.log_file, level=args.log_level)
    automatic(
        changeset=args.changeset,
        loc=args.remote,
        ops=args.branch_operational,
        repo=args.repository_dir,
        spawn=_spawn,
        stable=args.branch_stable,
        test=args.branch_test,
    )
else:
    import dawgie.tools.compliant

    pass
