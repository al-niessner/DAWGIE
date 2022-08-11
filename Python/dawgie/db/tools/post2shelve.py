#!/usr/bin/env python3
'''
COPYRIGHT:
Copyright (c) 2015-2022, California Institute of Technology ("Caltech").
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

# it works and needs to be redone when shelf is update to support all the
# functionality in postgres. Therefore pylint: disable=consider-using-f-string

import argparse
import logging
import os
import shelve
import sys

class Yo:
    # pylint: disable=too-few-public-methods
    def __init__(self, v):
        self.design = v[3]
        self.implementation = v[4]
        self.bugfix = v[5]

    def __lt__(self, other):
        return self.design < other.design or \
               (self.design == other.design and
                self.implementation < other.implementation) or \
               (self.design == other.design and
                self.implementation == other.implementation and
                self.bugfix < other.bugfix)

    def __str__(self):
        return '.'.join([str(self.design),
                         str(self.implementation),
                         str(self.bugfix)])
    pass

def convert_algorithm_db(conn, fn):
    ''' Task.Alg '''
    # pylint: disable=protected-access
    cur = dawgie.db.post._cur(conn)
    cur.execute('SELECT * from %s;' % 'Algorithm')
    rows = cur.fetchall()
    d = shelve.open(fn)
    tdb = {}
    for r in rows:
        y = Yo(r)
        cur.execute('SELECT PK,NAME from %s WHERE PK=%d' % ('Task', r[2]))
        foreign_name = cur.fetchone()[1]
        name = '.'.join([foreign_name, r[1]])
        k = r[0]
        if k not in tdb:
            tdb[k] = {'alg_pk':r[0], 'yo':y, 'name':name}
            d[name] = ['%s' % y]
        elif tdb[k]['yo'] < y:
            tdb[k] = {'alg_pk':r[2], 'yo':y, 'name':name}
            d[name] = ['%s' % y]

    conn.commit()
    cur.close()
    return tdb

def convert_target_db(conn, fn):
    # pylint: disable=protected-access
    cur = dawgie.db.post._cur(conn)
    cur.execute('SELECT * from %s;' % 'Target')
    rows = cur.fetchall()
    d = shelve.open(fn)
    tdb = {}
    for r in rows:
        k = r[1]
        d[k] = None
        tdb[r[0]] = {'target_pk':r[0], 'name':k}
    d.close()
    conn.commit()
    cur.close()
    return tdb

def convert_task_db(conn, fn):
    # pylint: disable=protected-access
    cur = dawgie.db.post._cur(conn)
    cur.execute('SELECT * from %s;' % 'Task')
    rows = cur.fetchall()
    d = shelve.open(fn)
    tdb = {}
    for r in rows:
        k = r[1]
        d[r[1]] = None
        tdb[r[0]] = {'task_pk':r[0], 'name':k}
    d.close()
    conn.commit()
    cur.close()
    return tdb

def convert_state_vector_db(conn, fn, alg_k):
    ''' Task.Alg.State '''
    # pylint: disable=protected-access
    cur = dawgie.db.post._cur(conn)
    alg_info = {}
    alg_pk = []
    for k,v in alg_k.items():
        alg_info[v['alg_pk']] = v['name']
        alg_pk.append(str(v['alg_pk']))
    cur.execute("SELECT * from StateVector where alg_ID = ANY('{%s}'::int[]);" % ','.join(alg_pk))
    rows = cur.fetchall()
    d = shelve.open(fn)
    tdb = {}
    for r in rows:
        y = Yo(r)
        k = '.'.join([alg_info[r[2]], r[1]])
        tdb[r[0]] = {'state_pk':r[0], 'yo':y, 'name':k}
        d[k] = ['%s' % y]

    conn.commit()
    cur.close()
    return tdb

def convert_value_vector_db(conn, fn, state_k):
    ''' Task.Alg.State.Value '''
    # pylint: disable=protected-access
    cur = dawgie.db.post._cur(conn)
    state_info = {}
    state_pk = []
    for k,v in state_k.items():
        state_info[v['state_pk']] = v['name']
        state_pk.append(str(v['state_pk']))
    cur.execute("SELECT * from Value where sv_ID = ANY('{%s}'::int[]);" %
                ','.join(state_pk))
    rows = cur.fetchall()
    d = shelve.open(fn)
    tdb = {}
    for r in rows:
        y = Yo(r)
        k = '.'.join([state_info[r[2]], r[1]])
        tdb[r[0]] = {'value_pk':r[0], 'yo':y, 'name':k}
        d[k] = ['%s' % y]

    conn.commit()
    cur.close()
    return tdb

def convert_prime_db(conn, fn, data):
    ''' run_id.Target.Task.Alg.State.Value blob_name '''
    # pylint: disable=protected-access,too-many-locals
    cur = dawgie.db.post._cur(conn)
    table = {}
    task_IDs = [str(v['task_pk']) for k,v in data['task'].items()]
    tn_IDs = [str(v['target_pk']) for k,v in data['target'].items()]
    alg_IDs = [str(v['alg_pk']) for k,v in data['alg'].items()]
    sv_IDs = [str(v['state_pk']) for k,v in data['state'].items()]
    val_IDs = [str(v['value_pk']) for k,v in data['value'].items()]

    value_info = {}
    value_pk = []
    for k,v in data['value'].items():
        value_info[v['value_pk']] = v['name']
        value_pk.append(str(v['value_pk']))

    cur.execute("SELECT PK,tn_ID,task_ID,alg_ID,sv_ID,val_ID,run_ID,blob_name from Prime where " +
                "tn_ID = ANY('{%s}'::int[]) " % (','.join(tn_IDs)) +
                "and task_ID = ANY('{%s}'::int[]) " % (','.join(task_IDs)) +
                "and alg_ID = ANY('{%s}'::int[]) " % (','.join(alg_IDs)) +
                "and sv_ID = ANY('{%s}'::int[]) " % (','.join(sv_IDs)) +
                "and val_ID = ANY('{%s}'::int[]) " % (','.join(val_IDs)))
    rows = cur.fetchall()
    tdb = {}
    for r in sorted (rows, key=lambda r:r[0]):
        y = Yo(r)
        rid = r[-2]
        k = '.'.join(['1' if rid else '0',
                      data['target'][r[1]]['name'],
                      data['value'][r[5]]['name']])
        tdb[k] = {'prime_pk':r[0], 'yo':y, 'name':k}
        table[k] = '%s'% (r[-1])

    conn.commit()
    cur.close()
    with shelve.open(fn) as db: db.update (table)
    return tdb

def main(dpath):
    # pylint: disable=protected-access
    conn = dawgie.db.post._conn()
    os.system("mkdir -p %s" % dpath)
    os.system("rm %s/%s.target" % (dpath, dawgie.context.db_post2shelve_prefix))
    os.system("rm %s/%s.task" % (dpath, dawgie.context.db_post2shelve_prefix))
    os.system("rm %s/%s.alg" % (dpath, dawgie.context.db_post2shelve_prefix))
    os.system("rm %s/%s.state" % (dpath, dawgie.context.db_post2shelve_prefix))
    os.system("rm %s/%s.value" % (dpath, dawgie.context.db_post2shelve_prefix))
    os.system("rm %s/%s.prime" % (dpath, dawgie.context.db_post2shelve_prefix))

    logging.getLogger(__name__).info('-------------target-----------')
    target_k = convert_target_db(conn, '%s/%s.target' % (dpath, dawgie.context.db_post2shelve_prefix))
    logging.getLogger(__name__).info('-------------task-----------')
    task_k = convert_task_db(conn, '%s/%s.task' % (dpath, dawgie.context.db_post2shelve_prefix))
    logging.getLogger(__name__).info('-------------alg-----------')
    alg_k = convert_algorithm_db(conn, '%s/%s.alg' % (dpath, dawgie.context.db_post2shelve_prefix))
    logging.getLogger(__name__).info('-------------state-----------')
    state_k = convert_state_vector_db(conn, '%s/%s.state' % (dpath, dawgie.context.db_post2shelve_prefix), alg_k)
    logging.getLogger(__name__).info('-------------value-----------')
    value_k = convert_value_vector_db(conn, '%s/%s.value' % (dpath, dawgie.context.db_post2shelve_prefix), state_k)
    logging.getLogger(__name__).info('-------------prime-----------')
    d = {'target':target_k,
         'task':task_k,
         'alg':alg_k,
         'state':state_k,
         'value':value_k}
    logging.getLogger(__name__).info('-------------convert-----------')
    convert_prime_db (conn,
                      dpath+'/%s.prime' % dawgie.context.db_post2shelve_prefix,
                      d)
    conn.close()
    pass

if __name__ == "__main__":
    # main blocks always look the same; pylint: disable=duplicate-code
    root = os.path.dirname (__file__)
    for i in range(4): root = os.path.join (root, '..')
    root = os.path.abspath (root)
    sys.path.append (root)

    import dawgie.context
    import dawgie.db
    import dawgie.db.tools.util
    import dawgie.util
    import dawgie.db.post

    ap = argparse.ArgumentParser(description='Translates postgresql database to shelve database. This is a one-way translation, no way to go back.')
    ap.add_argument ('-l', '--log-file', default=None, required=False,
                     help='a filename to put all of the log messages into [stdout]')
    ap.add_argument ('-L', '--log-level', default=logging.WARNING,
                     required=False, type=dawgie.util.log_level,
                     help='set the verbosity that you want where a smaller number means more verbose [logging.WARNING]')
    ap.add_argument ('-O', '--output-path', required=True, type=str,
                     help='a path to place your converted shelve files into')
    ap.add_argument ('-p', '--prefix',
                     default=dawgie.context.db_post2shelve_prefix,
                     required=False,
                     help='a filename prefix to put all the post2shelve db files into [%(default)s]')
    dawgie.context.add_arguments (ap)
    args = ap.parse_args()
    dawgie.context.override (args)
    dawgie.context.db_post2shelve_prefix = args.prefix
    main(args.output_path)
else:
    import dawgie.context
    import dawgie.db.post
    pass
