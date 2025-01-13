#! /usr/bin/env python3
'''Reduce the log files to something meaningful quickly

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


def filename(fn):
    return fn


def main():
    ap = argparse.ArgumentParser(
        description='Reduce a log file to something more meaningful using simple filtering defined at the command line. The entire pipeline system is built around the python logging facility. The problem with that is the logs get very large and contain lots of messages that are not very interesteding at this moment but will be at another momement. This tool allows the user to filter dowen the messages to just those that are of concern now.'
    )
    ap.add_argument(
        '-f',
        '--file-name',
        required=True,
        type=filename,
        help='full path to the log file to reduce',
    )
    ap.add_argument(
        '-id',
        '--ignore-debug',
        action='store_true',
        default=False,
        required=False,
        help='ignore all debug messages',
    )
    ap.add_argument(
        '-ii',
        '--ignore-info',
        action='store_true',
        default=False,
        required=False,
        help='ignore all info messages',
    )
    ap.add_argument(
        '-iw',
        '--ignore-warning',
        action='store_true',
        default=False,
        required=False,
        help='ignore all warning messages',
    )
    ap.add_argument(
        '-ie',
        '--ignore-error',
        action='store_true',
        default=False,
        required=False,
        help='ignore all error messages',
    )
    ap.add_argument(
        '-ic',
        '--ignore-critical',
        action='store_true',
        default=False,
        required=False,
        help='ignore all critical messages',
    )
    ap.add_argument(
        '-is',
        '--ignore-scrape',
        action='store_true',
        default=False,
        required=False,
        help='ignore the missing URI scrape errors',
    )
    ap.add_argument(
        '-im',
        '--ignore-module',
        default=[],
        nargs='*',
        help='ignore packages like "dawgie.ae.deroo.fit"',
    )
    ap.add_argument(
        '-it',
        '--ignore-text',
        default=[],
        nargs='*',
        help='ignore text in the message part of the log entry',
    )
    args = ap.parse_args()
    ignore = {
        'DEBUG': args.ignore_debug,
        'INFO': args.ignore_info,
        'WARNING': args.ignore_warning,
        'ERROR': args.ignore_error,
        'CRITICAL': args.ignore_critical,
        'scrape': args.ignore_scrape,
        'module': args.ignore_module,
        'text': args.ignore_text,
    }
    for m in reduce(args.file_name, ignore):
        print(''.join(m))
    return


LEVELS = ['DEBUG:', 'INFO:', 'WARNING:', 'ERROR:', 'CRITICAL:']


def reduce(fn, ignore):
    with open(fn, 'rt', encoding="utf-8") as f:
        m = []
        t = False
        for line in f.readlines():
            if any((line.startswith(lvl) for lvl in LEVELS)):
                if m and t:
                    yield m

                lvl = line[: line.find(':')]
                mod = line[
                    len(lvl) + 1 : line[len(lvl) + 1 :].find(':') + len(lvl) + 1
                ]
                msg = line[len(lvl) + len(mod) + 2 :]
                t = not ignore[lvl]
                t &= line.find('scrape this URI:') < 0
                t &= all((im != mod for im in ignore['module']))
                t &= all((msg.find(it) < 0 for it in ignore['text']))
                m.clear()
                m.append(line)
                pass
            else:
                m.append(line)
            pass
        pass
    return


if __name__ == '__main__':
    main()
