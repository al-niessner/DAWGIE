#! /usr/bin/env python3
'''

COPYRIGHT:
Copyright (c) 2015-2020, California Institute of Technology ("Caltech").
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


def read_requirements():
    requirements = []
    with open('./requirements.txt', 'rt') as file:
        for line in file:
            # exclude comments
            line = line[:line.find("#")] if "#" in line else line
            # clean
            line = line.strip()
            if line:
                requirements.append(line)
    return requirements


dawgie = os.path.join('dawgie', '__init__.py')
version = os.environ.get('DAWGIE_VERSION', '0.0.0')
with open(os.path.join(os.path.dirname(__file__), dawgie)) as f:
    t = f.read()
t = t.replace("'0.0.0'", "'{0}'".format(version))
with open(os.path.join(os.path.dirname(__file__), dawgie), 'tw') as f:
    f.write(t)

# first item in list must be README file name
data_files_names = ["README.md", "LICENSE.txt"]
data_files_locations = [('.', [f]) if os.path.exists(f) else
                        ('.', ["../" + f]) for f in data_files_names]

read_me_file = data_files_names[0] if os.path.exists(data_files_names[0]) else \
    f"../{data_files_names[0]}"
with open(read_me_file, "rt") as f:
    description = f.read()

deps = read_requirements()
setuptools.setup(name='dawgie',
                 version=version,
                 packages=['dawgie',
                           'dawgie.db',
                           'dawgie.db.tools',
                           'dawgie.de',
                           'dawgie.fe',
                           'dawgie.pl',
                           'dawgie.pl.logger',
                           'dawgie.tools'],
                 setup_requires=deps,
                 src_root=os.path.abspath(os.path.dirname(__file__)),
                 install_requires=deps,
                 package_data={'dawgie.pl': ['state.dot'],
                               'dawgie.fe': ['fonts/open*', 'fonts/bootstrap/*',
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
                 data_files=data_files_locations,
                 description='Data and Algorithm Work-flow Generation, Introspection, and Execution (DAWGIE)',
                 license='see LICENSE file for details',
                 long_description=description,
                 long_description_content_type="text/markdown",
                 keywords='adaptive pipeline',
                 url='https://github.com/al-niessner/DAWGIE')
