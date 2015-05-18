#!/usr/bin/env python
# coding: utf-8
from setuptools import setup, find_packages

# PBR does not work with VCS requirements, yet:
# https://bugs.launchpad.net/pbr/+bug/1373623
# setup(setup_requires=['pbr'], pbr=True)


def content_of_file(filename):
    with open(filename) as f:
        return f.read()

setup(
    name='lib',
    version='0.0.1',
    description='Data package tool',
    long_description=content_of_file('README.md'),
    author='Krisztián Fekete',
    author_email='krisztian.fekete@gmail.com',
    url='https://github.com/krisztianfekete/lib',
    license=content_of_file('LICENSE'),
    packages=find_packages(exclude=('tests', 'docs')),

    install_requires=[
        'appdirs==1.4.0',
        'argh==0.26.1',
        'omlite',
    ],
    dependency_links=[
        'git+https://github.com/krisztianfekete/omlite#egg=omlite',
    ],
    classifiers=[
        'Development Status :: 1 - Planning',
        'Environment :: Console',
        'License :: Public Domain',
    ],
    entry_points={
        'console_scripts': [
            'ws = lib.tool.ws:main'
        ]
    }
)
