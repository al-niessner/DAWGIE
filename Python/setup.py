#! /usr/bin/env python3
'''

COPYRIGHT:
Copyright (c) 2015-2019, California Institute of Technology ("Caltech").
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

import os
import setuptools

base = 'DAWGIE-'
dawgie = os.path.join ('dawgie', '__init__.py')
deps = ['bokeh==0.13.0',
        'boto3>=1.7.80',
        'GitPython>=2.1.11',
        'gnupg>=2.3.1',
        'psycopg2>=2.7.4',
        'pydot3==1.0.9',
        'requests==2.19.1',
        'transitions==0.6.8',
        'twisted>=18.7.0',
        ]
version = 'ghrVersion'

if version == 'ghr' + 'Version':
    version = os.path.basename (os.path.abspath
                                (os.path.join (os.path.dirname (__file__),
                                               '..')))
    version = version[len(base):] if version.startswith (base) else '0.0.0'
    pass

with open (os.path.join (os.path.dirname (__file__), dawgie)) as f: t = f.read()
t = t.replace ('${UNDEFINED}', version)
with open (os.path.join (os.path.dirname (__file__), dawgie), 'tw') as f:\
     f.write (t)
setuptools.setup (name='dawgie',
                  version=version,
                  packages=['dawgie',
                            'dawgie.db', 'dawgie.db.tools',
                            'dawgie.de',
                            'dawgie.fe',
                            'dawgie.pl', 'dawgie.pl.logger',
                            'dawgie.tools'],
                  setup_requires=deps,
                  src_root=os.path.abspath (os.path.dirname (__file__)),
                  install_requires=deps,
                  package_data={'dawgie.pl':['state.dot'],
                                'dawgie.fe':['fonts/open*','fonts/bootstrap/*',
                                             'images/*.jpg',
                                             'images/*.gif',
                                             'images/svg/*',
                                             'javascripts/*.js',
                                             'javascripts/templates/*',
                                             'pages/index.html',
                                             'pages/about/index.html',
                                             'pages/algorithms/index.html',
                                             'pages/command/index.html',
                                             'pages/database/index.html',
                                             'pages/database/primary_table/index.html',
                                             'pages/database/targets/index.html',
                                             'pages/database/tasks/index.html',
                                             'pages/database/versions/index.html',
                                             'pages/exoplanet_systems/index.html',
                                             'pages/logs/index.html',
                                             'pages/news/index.html',
                                             'pages/pipelines/index.html',
                                             'pages/schedule/index.html',
                                             'pages/search/index.html',
                                             'pages/tasks/index.html',
                                             'stylesheets/*.css']},
                  author='Al Niessner',
                  author_email='Al.Niessner@jpl.nasa.gov',
                  description='Data and Algorithm Work-flow Generation, Introspection, and Execution (DAWGIE) -- dynamically schedules dawgie.Tasks to be done a worker farm (cloud) and persists the dawgie.Values within the dawgie.StateVectors generated from the dawgie.Algorithms that make up the dawgie.Task.',
                  license='''*******************************************************************************
 **
 **          Copyright 2017, by the California Institute of Technology
 **    ALL RIGHTS RESERVED. United States Government Sponsorship acknowledged.
 ** Any commercial use must be negotiated with the Office of Technology Transfer
 **                  at the California Institute of Technology.
 **
 **  This software may be subject to U.S. export control laws and regulations.
 **  By accepting this document, the user agrees to comply with all applicable
 **                        U.S. export laws and regulations.
 **   User has the responsibility to obtain export licenses, or other export
 **  authority as may be required before exporting such information to foreign
 **                countries or providing access to foreign persons.
 ******************************************************************************
 ** NTR: 50482''',
                  keywords='adaptive pipeline',
                  url='https://github.jpl.nasa.gov/niessner/SDS')
