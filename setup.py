#!/usr/bin/env python
from setuptools import setup, find_packages
import os, re

PKG='simplegeo'
VERSIONFILE = os.path.join('simplegeo', '_version.py')
verstr = "unknown"
try:
    verstrline = open(VERSIONFILE, "rt").read()
except EnvironmentError:
    pass # Okay, there is no version file.
else:
    MVSRE = r"^manual_verstr *= *['\"]([^'\"]*)['\"]"
    mo = re.search(MVSRE, verstrline, re.M)
    if mo:
        mverstr = mo.group(1)
    else:
        print "unable to find version in %s" % (VERSIONFILE,)
        raise RuntimeError("if %s.py exists, it must be well-formed" % (VERSIONFILE,))
    AVSRE = r"^auto_build_num *= *['\"]([^'\"]*)['\"]"
    mo = re.search(AVSRE, verstrline, re.M)
    if mo:
        averstr = mo.group(1)
    else:
        averstr = ''
    verstr = '.'.join([mverstr, averstr])

setup_requires = []
tests_require = ['mock']

# nosetests is an optional way to get code-coverage results. Uncomment
# the following and run "python setup.py nosetests --with-coverage.
# --cover-erase --cover-tests --cover-inclusive --cover-html"
# tests_require.extend(['coverage', 'nose'])

# trialcoverage is another optional way to get code-coverage
# results. Uncomment the following and run "python setup.py trial
# --reporter=bwverbose-coverage -s simplegeo.test".
# setup_requires.append('setuptools_trial')
# tests_require.extend(['setuptools_trial', 'trialcoverage'])

# As of 2010-11-22 neither of the above options appear to work to
# generate code coverage results, but the following does:
# rm -rf ./.coverage* htmlcov ; coverage run --branch  --include=simplegeo/* setup.py test ; coverage html

setup(name=PKG,
      version=verstr,
      description="Library for interfacing with SimpleGeo's API",
      author="Zooko Wilcox-O'Hearn and Ben Standefer",
      author_email="ben@simplegeo.com",
      url="http://github.com/simplegeo/python-simplegeo",
      packages = find_packages(),
      license = "MIT License",
      install_requires=['httplib2>=0.6.0', 'oauth2>=1.5', 'pyutil[jsonutil] >= 1.8.1', 'ipaddr >= 2.0.0'],
      keywords="simplegeo",
      zip_safe=False, # actually it is zip safe, but zipping packages doesn't help with anything and can cause some problems (http://bugs.python.org/setuptools/issue33 )
      test_suite='simplegeo.test',
      setup_requires=setup_requires,
      tests_require=tests_require)
