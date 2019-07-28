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

dawgie = os.path.join ('dawgie', '__init__.py')
deps = ['bokeh>=1.2',
        'boto3>=1.7.80',
        'cryptography>=2.1.4',
        'dawgie-pydot3==1.0.10',
        'GitPython>=2.1.11',
        'matplotlib>=2.1.1',
        'psycopg2>=2.7.4',
        'pyparsing>=2.2',
        'python-gnupg==0.4.4',
        'pyxb==1.2.6',
        'requests>=2.20.0',
        'transitions==0.6.8',
        'twisted>=18.7.0',
        ]
version = os.environ.get ('DAWGIE_VERSION', '0.0.0')
with open (os.path.join (os.path.dirname (__file__), dawgie)) as f: t = f.read()
t = t.replace ("'0.0.0'", "'{0}'".format (version))
with open (os.path.join (os.path.dirname (__file__), dawgie), 'tw') as f:\
     f.write (t)
with open (os.path.join (os.path.dirname (__file__), 'README.md'), 'rt') as f:\
     description = f.read()

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
                  classifiers=["Programming Language :: Python :: 3",
                               "Operating System :: OS Independent",
                               'License :: Free To Use But Restricted',
                               'Development Status :: 5 - Production/Stable'],
                  data_files=[('.', ['LICENSE', 'README.md'])],
                  description='Data and Algorithm Work-flow Generation, Introspection, and Execution (DAWGIE)',
                  license='see LICENSE file for details',
                  long_description=description,
                  long_description_content_type="text/markdown",
                  keywords='adaptive pipeline',
                  url='https://github.com/al-niessner/DAWGIE')
