#! /usr/bin/env python3
'''tool to inter data for a mausoleum'''

import argparse
import os
import shutil
import sys

def _clean(line:str)->str:
    '''clean up an item to remove comments and end of line if read from stdin'''
    if '#' in line: line = line[:line.find('#')]
    return line.strip()

def _compare (base:str, wild:str):
    match = False

    if wild == '*': match = True
    elif '*' in wild:
        front = wild[:wild.find ('*')]
        back = wild[wild.find ('*') + 1:]

        if not front: match = base.endswith (back)
        elif not back: match = base.startswith (front)
        else: match = base.startswith (front) and match.endswith (back)
    else: match = base == wild

    return match

def _file(filename:str)->str:
    '''does the file exist and is it a real file'''
    if not os.path.exists(filename):
        raise ValueError('File "' + filename + '" does not exist')
    if not os.path.isfile(filename):
        raise ValueError('"' + filename + '" is not a regular file')
    return filename

def _path(path:str)->str:
    '''does the path exist and is it a directory'''
    if not os.path.exists(path):
        raise ValueError('Path "' + path + '" does not exist')
    if not os.path.isdir(path):
        raise ValueError('"' + path + '" is not a directory')
    return path

def _ref (ident:str)->str:
    '''make sure an item is a complete reference in DAWGIE terms'''
    if ident.count ('.') != 5: raise ValueError('Malformed reference: ' + ident)
    return ident

def copy_blobs (blobs:[str], blobpath:str, outpath:str)->None:
    for bfn in blobs:
        ifn = os.path.join (blobpath, bfn)
        ofn = os.path.join (os.path.join (outpath, 'dbs'), bfn)

        if not os.path.exists (ofn) and os.path.isfile (ifn):
            shutil.copy (ifn, ofn)
            pass
        pass
    return

def mkdirs (outpath:str)->None:
    for subdir in ['db', 'dbs', 'fe', 'logs', 'stg']:
        fullpath = os.path.join (outpath, subdir)
        if not os.path.exists (fullpath): os.mkdir (fullpath)
        pass
    return

def postgres (args:argparse.Namespace, items:[str], outdir:str)->[str]:
    '''inter postgresql dataset'''
    # Need two pasees to decode a postgresql backup file. First pass will change
    # the item name, specifically target, task, alg, sv, and value names, to
    # table primary key. These are needed because the DAWGIE primary table uses
    # foriegn keys instead of the actual names to better handle versions.
    blobs = []
    ifn = 'interred.' + os.path.basename (args.backup_file)
    seconds = postgres_extract_secondary_tables (args.backup_file)
    with open (os.path.join
               (os.path.join (outdir, 'db'), ifn), 'tw') as output_file:
        key = ''
        with open (args.backup_file, 'rt') as input_file:
            for line in input_file.readlines():
                if line.startswith ('\\.'): key = ''
                elif line.startswith ('COPY public.prime'): key = 'prime'
                elif key:
                    reference,blob_name = postgres_translate (line, seconds)

                    if postgres_is_match (reference, items):
                        blobs.append (blob_name)
                    else: line = None
                    pass

                if line is not None: output_file.write (line)
                pass
            pass
        pass
    return blobs

def postgres_extract_secondary_tables (filename:str)->{}:
    '''build a lookup table from name to set of foriegn keys'''
    key = ''
    tables = {'target':{},
              'task':{},
              'algorithm':{},
              'statevector':{},
              'value':{}}
    with open (filename, 'rt') as file:
        for line in file.readlines():
            if line.startswith ('\\.'): key = ''
            elif line.startswith ('COPY public.'):
                key = line.split()[1].split('.')[1]
                key = key if key in tables else ''
            elif key:
                pkey,name = line.strip().split('\t')[:2]
                tables[key][pkey] = name
                pass
            pass
        pass
    return tables

def postgres_is_match (ref:str, items:[str])->bool:
    '''does this ref match any of the items'''
    matches = []
    sref = ref.split('.')
    for item in items:
        matches.append (all([_compare (r,i) for r,i in zip(sref,
                                                           item.split('.'))]))
        pass
    return any(matches)

def postgres_translate (row:str, tables:{})->str:
    '''translate from a Prime table row to a simple string with . delimiting'''
    _pk,run_id,task_id,tn_id,alg_id,sv_id,val_id,blob_name = row.strip().split()
    return '.'.join ([run_id,
                      tables['target'][tn_id],
                      tables['task'][task_id],
                      tables['algorithm'][alg_id],
                      tables['statevector'][sv_id],
                      tables['value'][val_id]]),blob_name

if __name__ == '__main__':
    AP = argparse.ArgumentParser(description=__doc__)
    CMD = AP.add_subparsers(help='database to be interred', title='commands')
    PDB = CMD.add_parser('postgres', help='inter a set of postgresql data')
    PDB.add_argument('-b', '--backup-file', default='', type=_file,
                     help='postgresql backup file made with pgdump')
    PDB.set_defaults(func=postgres)
    AP.add_argument ('-B', '--blob-path', required=True, type=_path,
                     help='path to the blob data that the database references')
    AP.add_argument ('-O', '--output-path', required=True, type=_path,
                     help='path to output inter information')
    AP.add_argument ('items', default=[sys.stdin], metavar='items', nargs='*',
                     type=_ref, help='list of references to inter to the mausoleum where they must be fully qualified with runid.target.task.alg.sv.value and "*" can be used for any of those 6 fields with *.*.*.*.*.* matching everything.')  # pylint: disable=line-too-long
    ARGS = AP.parse_args()

    if ARGS.items[0] == sys.stdin:
        print ('Reading items to inter from stdin...')
        ARGS.items.clear()
        ITEMS = [_clean (line) for line in sys.stdin.readlines()]
        ARGS.items.extend ([_ref(item) for item in filter (lambda s:s, ITEMS)])
        pass
    mkdirs (ARGS.output_path)
    copy_blobs (ARGS.func (ARGS, ITEMS, ARGS.output_path),
                ARGS.blob_path, ARGS.output_path)
    pass
