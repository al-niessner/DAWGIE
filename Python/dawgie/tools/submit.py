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

OPS = "main"
PRE_OPS = "pre_ops"
REPO_DIR = "/proj/src/ws"
ORIGIN = "origin"
OPS_DIR = "/proj/src/ae"


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


def _main(an_args):
    # being a main, imports are later so pylint: disable=used-before-assignment
    # 1. Run auto merge tool
    status = dawgie.tools.submit.auto_merge_prepare(
        an_args.changeset, an_args.PRE_OPS, an_args.REPO_DIR, an_args.ORIGIN
    )

    if status == State.SUCCESS:
        status = dawgie.tools.submit.auto_merge_compliant(
            an_args.changeset, an_args.REPO_DIR, _spawn
        )
    if status == State.SUCCESS:
        status = dawgie.tools.submit.auto_merge_push(
            an_args.changeset, an_args.REPO_DIR
        )

    if status == State.SUCCESS:
        # 2. Update master
        if dawgie.tools.submit.update_ops() != State.SUCCESS:
            mail_out("update_ops failed.")
    else:
        mail_out("Automerge failed; so, failed to update_ops.")
    return


def _spawn(cmd: [str]):
    return subprocess.call(cmd) == 0


def already_applied(changeset, a_repo_dir):
    g = git.cmd.Git(a_repo_dir)
    gl = g.execute('git log'.split())
    return -1 < gl.find(changeset)


def auto_merge_prepare(
    changeset, a_pre_ops=None, a_repo_dir=None, a_origin=None
):
    # pylint: disable=too-many-return-statements
    if not a_pre_ops or not a_repo_dir or not a_origin:
        mail_out("auto_merge parameters are not all defined.")
        return State.FAILED

    g = git.cmd.Git(a_repo_dir)

    # Up to date
    status = git_execute(g, "git fetch")
    if status == State.FAILED:
        logging.info("Failed to fetch")
        return State.FAILED

    # Check if commit exists
    status = git_execute(g, f'git cat-file -t {changeset}')
    if status == State.FAILED:
        mail_out(
            f"You forgot to push your changes ({changeset}). Please, push them."
        )
        return State.FAILED

    # Check-out PRE_OPS
    status = git_execute(g, f"git checkout {a_pre_ops}")
    if status == State.FAILED:
        mail_out(f"Failed to checkout {a_pre_ops}")
        return State.FAILED

    # Make sure checkout is clean.
    status = git_execute(g, f"git pull {ORIGIN} {a_pre_ops}")
    if status == State.FAILED:
        mail_out(f"Failed to pull in {a_pre_ops}")
        return State.FAILED

    # Merge with changeset
    commit_msg = f"merging_{changeset}_into_{a_pre_ops}"
    status = git_execute(g, f"git merge -m {commit_msg} {changeset}")
    if status == State.FAILED:
        msg = "Failed to merge " + changeset + " into " + a_pre_ops + "."
        msg += " You probably have merge conflicts. Please update and merge"
        msg += " master into your branch and try again.\n"
        msg += "Aborting merge."
        status = git_execute(g, "git merge --abort")
        if status == State.FAILED:
            msg += "\nFailed to abort merge. Take Action! Take Action!"

        mail_out(msg)
        return State.FAILED
    return State.SUCCESS


def auto_merge_compliant(changeset, a_repo_dir, spawn):
    g = git.cmd.Git(a_repo_dir)
    # Validate compliance
    # run compliance
    # if failed then revert git reset --hard ORIG_HEAD
    # otherwise continue
    if not dawgie.tools.compliant.verify(a_repo_dir, True, False, spawn):
        msg = f"Compliancy check failed. Please run compliant.py for ({changeset})"
        status = git_execute(g, "git reset --hard ORIG_HEAD")
        if status == State.FAILED:
            msg += " And also failed to do a git reset. Please check this out Keepers of the Pipelie."
        mail_out(msg)
        return State.FAILED
    return State.SUCCESS


def auto_merge_push(
    changeset, a_pre_ops=None, a_repo_dir=None, priority=Priority.TODO.value
):
    g = git.cmd.Git(a_repo_dir)
    status = git_execute(g, f"git checkout {a_pre_ops}")
    if status == State.FAILED:
        mail_out(f"Failed to checkout {a_pre_ops}")
        return State.FAILED

    # Push changes
    status = git_execute(g, f"git push {ORIGIN} {a_pre_ops}")
    if status == State.FAILED:
        mail_out(f"Failed to push changes to {a_pre_ops}")
        return State.FAILED

    # Mail out the good news
    cmd = f'git show --no-patch {changeset}'
    status = git_execute(g, cmd)
    if status == State.FAILED:
        mail_out(f"Failed to run: {cmd}")
        return State.FAILED

    mail_out(
        f"Successfully merged {changeset} into {a_pre_ops}. The pipeline is reloading with your changes based on the scheduled priority.\nSubmission asks for the pipeline to reload: {priority}.\n"
        + g.execute(cmd.split(' '))
    )
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
        logging.critical('Missing email destination: %s', str(msg))
    return


def merge_into(g, src, dst):
    status = git_execute(g, f"git merge {ORIGIN}/{src}")
    if status == State.FAILED:
        msg = f"Failed to merge {src} into {dst}."

        if git_execute(g, "git merge --abort") == State.FAILED:
            msg += "\nFailed to abort merge. Take Action! Take Action!"
        mail_out(msg)
        pass
    return status


def update_ops():
    g = git.cmd.Git(REPO_DIR)

    # Up to date
    status = git_execute(g, "git fetch")
    if status == State.FAILED:
        logging.info("update_ops: Failed to fetch on %s", REPO_DIR)
        return State.FAILED

    # merge OPS into PRE_OPS
    if merge_into(g, OPS, PRE_OPS) == State.FAILED:
        return State.FAILED

    # push PRE_OPS
    status = git_execute(g, f"git push {ORIGIN} {PRE_OPS}")

    # Now update the real thing
    g = git.cmd.Git(OPS_DIR)

    # Up to date
    status = git_execute(g, "git fetch")
    if status == State.FAILED:
        logging.info("update_ops: Failed to fetch on %s", OPS_DIR)
        return State.FAILED

    # merge PRE_OPS into OPS
    if merge_into(g, PRE_OPS, OPS) == State.FAILED:
        return State.FAILED

    # push OPS
    if git_execute(g, f"git push {ORIGIN} {OPS}") == State.FAILED:
        mail_out(f"update_ops: Failed to push to {OPS}")
        return State.FAILED

    return State.SUCCESS


if __name__ == "__main__":
    import dawgie.context
    import dawgie.tools.compliant
    import dawgie.tools.submit
    import dawgie.util

    ap = argparse.ArgumentParser(
        description='Automatically merge changeset into PRE_OPS.'
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
        '-r',
        '--repo-dir',
        default=dawgie.tools.submit.REPO_DIR,
        required=False,
        help='set the PRE_OPS repo directory where you want to do the merging [%(default)s]',
    )
    ap.add_argument(
        '-m',
        '--ops-dir',
        default=dawgie.tools.submit.OPS_DIR,
        required=False,
        help='set the OPS repo directory where you want to do the merging [%(default)s]',
    )
    ap.add_argument(
        '-o',
        '--origin',
        default=dawgie.tools.submit.ORIGIN,
        required=False,
        help='The name of the ORIGIN. [%(default)s]',
    )
    ap.add_argument(
        '-M',
        '--ops',
        default=dawgie.tools.submit.OPS,
        required=False,
        help='The name of the OPS branch. [%(default)s]',
    )
    ap.add_argument(
        '-p',
        '--pre-ops',
        default=dawgie.tools.submit.PRE_OPS,
        required=False,
        help='The name of the PRE_OPS branch. [%(default)s]',
    )
    ap.add_argument(
        '-c',
        '--changeset',
        default=None,
        required=True,
        help='The changeset hashtag to merge.',
    )
    dawgie.context.add_arguments(ap)
    args = ap.parse_args()
    dawgie.context.override(args)
    dawgie.tools.submit.REPO_DIR = args.repo_dir
    dawgie.tools.submit.ORIGIN = args.origin
    dawgie.tools.submit.PRE_OPS = args.pre_ops
    dawgie.tools.submit.OPS = args.ops
    dawgie.tools.submit.OPS_DIR = args.ops_dir

    logging.basicConfig(filename=args.log_file, level=args.log_level)
    _main(args)
else:
    import dawgie.tools.compliant

    pass
