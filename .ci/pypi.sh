#! /usr/bin/env bash

if [[ $# -ne 1 ]]
then
    echo "usage: $0 <version>"
    echo "   where <version> is the release number to get from github.com"
    exit
fi

# sudo pip3 install -U twine wheel setuptools
export DAWGIE_VERSION=$1
#wdir=$(mkdtemp -d)
#cd $wdir
cd Python
cp ../README.md README.md
cat ../COPYRIGHT.txt > LICENSE
echo "" >> LICENSE
echo "" >> LICENSE
cat ../LICENSE.txt >> LICENSE
python3 setup.py sdist bdist_wheel
twine check dist/*
twine upload --verbose --repository-url https://test.pypi.org/legacy/ dist/*
#twine upload --verbose dist/*
#cd -
#rm -rf $wdir
