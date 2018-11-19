# -*- coding: latin-1 -*-
import sys
import codecs
import re
import os
from setuptools import setup

ver = sys.version_info
py_ver_major = ver[0]
if py_ver_major < 2:
    sys.exit(0)
py_ver_minor = ver[1]
if py_ver_major > 3:
    # for python >= 4.0, just assume 3.7
    py_ver_major = 3
    py_ver_minor = 7
if py_ver_major == 2:
    if py_ver_minor < 7:
        raise RuntimeError("SETUP PyLDAPI-Client: Python 2.6 or older is not supported.")
    ver_point = ver[2]
    if ver_point < 9:
        raise RuntimeError(
            "SETUP PyLDAPI-Client: When using Python 2.7, the v2.7.9 release is the minimum requirement.")
    add_packages = ['pyldapi_client.py27']
elif py_ver_major == 3:
    if py_ver_minor < 5:
        raise RuntimeError("SETUP PyLDAPI-Client: When using Python 3, the v3.5.x series is the minimum requirement.")
    add_packages = ['pyldapi_client.py35']
else:
    raise NotImplementedError("SETUP PyLDAPI-Client: Cannot use python version %s.%s" % (str(py_ver_major), str(py_ver_minor)))


def open_local(paths, mode='r', encoding='utf8'):
    path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        *paths
    )
    return codecs.open(path, mode, encoding)


with open_local(['pyldapi_client', '__init__.py'], encoding='latin1') as fp:
    try:
        version = re.findall(r"^__version__ = ['\"]([^']+)['\"]\r?$",
                             fp.read(), re.M)[0]
    except IndexError:
        raise RuntimeError('Unable to determine version.')

with open_local(['README.md']) as readme:
    long_description = readme.read()

with open_local(['requirements.txt']) as req:
    found_requirements = req.read().split("\n")
    dependency_links = []
    requirements = []
    for f in found_requirements:
        if 'git+' in f:
            pkg = f.split('#')[-1]
            dependency_links.append(f.strip() + '-9876543210')
            requirements.append(pkg.replace('egg=', '').rstrip())
        else:
            requirements.append(f.strip())

install_packages = ['pyldapi_client', 'pyldapi_client.functions']
install_packages.extend(add_packages)

setup(
    name='pyldapi-client',
    packages=install_packages,
    version=version,
    description='A Simple helper library for consuming registers, indexes, and instances of classes exposed via a pyldapi endpoint.',
    author='Ashley Sommer',
    author_email='ashley.sommer@csiro.au',
    url='https://github.com/CSIRO-enviro-informatics/pyldapi-client',
    download_url='https://github.com/CSIRO-enviro-informatics/pyldapi-client/'
                    'archive/v{:s}.tar.gz'.format(version),
    license='LICENSE.txt',
    keywords=['Linked Data', 'Semantic Web', 'Python',
              'Validate', 'HTTP', 'Client'],
    long_description=long_description,
    long_description_content_type='text/markdown',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Topic :: Utilities',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    install_requires=requirements,
    dependency_links=dependency_links
)

