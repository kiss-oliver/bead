#!/usr/bin/env python
# coding: utf-8
from __future__ import unicode_literals
from __future__ import print_function

import os
import stat
from subprocess import check_call
from glob import glob
import shutil
from zipfile import ZipFile, ZIP_DEFLATED
import contextlib


BUILD = 'executables'
PKGS = BUILD + '/pkgs'
SRC = BUILD + '/src'
TOOL_PYZ = BUILD + '/bead.pyz'
UNIX_TOOL = BUILD + '/bead'
WIN_TOOL = BUILD + '/bead.cmd'


def mkdir(dir):
    if not os.path.isdir(dir):
        os.makedirs(dir)


def pip(*args):
    return check_call(('pip',) + args)


def pip_download_source(*args):
    return pip('download', '--no-binary', ':all:', *args)


def rmtree(dir):
    shutil.rmtree(dir, ignore_errors=True)


def make_executable(file):
    st = os.stat(file)
    os.chmod(file, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


@contextlib.contextmanager
def notification(msg, long_output=False):
    if long_output:
        print(msg + ':')
        print()
        print('-' * 32)
    else:
        print(' * ' + msg)
    try:
        yield
    finally:
        if long_output:
            print('-' * 32)
            print()


def further_output(msg):
    return notification(msg, long_output=True)


progress = notification

# start with no build directory
rmtree(BUILD)

with further_output('Downloading dependencies'):
    mkdir(PKGS)
    pip_download_source('--dest', PKGS, '--exists-action', 'w', '-r', 'requirements.txt')

with further_output('Unpacking packages'):
    mkdir(SRC)
    for package in glob(PKGS + '/*') + ['.']:
        pip('install', '--target', SRC, '--no-compile', '--no-deps', package)

# # Get rid of the packaging junk
# for dir in glob(SRC + '/*.egg-info'):
#     rmtree(dir)

with progress('Creating .pyz zip archive from the sources ({})'.format(TOOL_PYZ)):
    with ZipFile(TOOL_PYZ, mode='w', compression=ZIP_DEFLATED) as zip:
        # add the entry point
        zip.write('__main__.py')
        # add python sources
        for realroot, dirs, files in os.walk(SRC):
            ziproot = os.path.relpath(realroot, SRC)
            for file_name in files:
                # if file_name.endswith('.py'):
                zip.write(
                    os.path.join(realroot, file_name),
                    os.path.join(ziproot, file_name))


def make_tool(tool_file_name, runner):
    with open(tool_file_name, 'wb') as f:
        f.write(runner)
        with open(TOOL_PYZ, 'rb') as pyz:
            f.write(pyz.read())


with progress('Creating unix tool ({})'.format(UNIX_TOOL)):
    UNIX_RUNNER = b'#!/usr/bin/env python\n'

    make_tool(UNIX_TOOL, UNIX_RUNNER)
    make_executable(UNIX_TOOL)

with progress('Creating windows tool ({})'.format(WIN_TOOL)):
    WINDOWS_RUNNER = b'\r\n'.join((
        b'@echo off',
        b'python.exe "%~f0" %*',
        b'exit /b %errorlevel%',
        b''))

    make_tool(WIN_TOOL, WINDOWS_RUNNER)

print('Done.')
