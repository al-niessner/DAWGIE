#! /usr/bin/env python3
'''
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

import argparse
import getpass
import logging
import os
import sys

def consumption():
    # pylint: disable=protected-access
    db = []
    dbs = []
    known = list(dawgie.db._prime_values())
    scrapes = {}
    for dp, dns, fns in os.walk (dawgie.context.data_dbs):
        for dn in dns: scrapes[dn] = scrapes.get (dn, [])

        for fn in fns:
            ffn = os.path.join (dp, fn)
            dbs.append (os.path.getsize (ffn))
            src = dp.split ('/')[-1]

            if src == 'dbs' and fn in known: db.append (dbs[-1])
            if src in scrapes: scrapes[src].append (dbs[-1])
            pass
        pass
    known = sum (db)
    lens = len (db)
    total = sum (dbs)
    # this is a tool and printing efficiency is less import then being explicit
    # in what is being output so pylint: disable=consider-using-f-string
    print ('\n\n\t\tFiles\tSize (GB)')
    print ('generated:\t{0:d}\t{1:5.1f}\t{2:3.1f}%'.format (len (db),
                                                            sum (db)/2**30,
                                                            sum(db)/total*100))
    for k in sorted (scrapes):
        known += sum (scrapes[k])
        lens += len (scrapes[k])
        print ('   {0:s}:\t{1:d}\t{2:5.1f}\t{3:3.1f}%'.format (k if 5 < len(k) else ('  ' + k),
                                                               len (scrapes[k]),
                                                               sum (scrapes[k])/2**30,
                                                               sum (scrapes[k])/total * 100))
        pass
    print ('  unknown:\t{0:d}\t{1:5.1f}\t{2:3.1f}%'.format (len (dbs) - lens,
                                                            (total - known)/2**30,
                                                            (1 - known/total) * 100))
    print ('------------------------------------------------')
    print ('    total:\t\t{0:d}\t{1:5.1f}\n\n\n'.format (len (dbs), total/2**30))
    return

if __name__ == '__main__':
    # main blocks always look the same; pylint: disable=duplicate-code
    root = os.path.dirname (__file__)
    for i in range(4): root = os.path.join (root, '..')
    root = os.path.abspath (root)
    sys.path.append (root)

    import dawgie.context
    import dawgie.db
    import dawgie.db.util
    import dawgie.util

    unique_fn = '.'.join (['dbsinfo', getpass.getuser(), 'log'])
    ap = argparse.ArgumentParser(description='Display interesting statistics about dbs.')
    ap.add_argument ('-l', '--log-file', default=unique_fn, required=False,
                     help='a filename to put all of the log messages into [%(default)s]')
    ap.add_argument ('-L', '--log-level', default=logging.INFO, required=False,
                     type=dawgie.util.log_level,
                     help='set the verbosity that you want where a smaller number means more verbose [logging.INFO]')
    dawgie.context.add_arguments (ap)
    args = ap.parse_args()
    dawgie.context.override (args)
    logging.basicConfig (filename=os.path.join (dawgie.context.data_log,
                                                args.log_file),
                         level=args.log_level)
    dawgie.db.open()
    consumption()
    dawgie.db.close()
    pass
