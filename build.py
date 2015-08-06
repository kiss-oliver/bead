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


BUILD = 'build'
PKGS = BUILD + '/pkgs'
SRC = BUILD + '/src'
CHECKOUT = BUILD + '/checkout'
TOOL_PYZ = BUILD + '/ws.pyz'
UNIX_TOOL = BUILD + '/ws'
WIN_TOOL = BUILD + '/ws.cmd'

def mkdir(dir):
    if not os.path.isdir(dir):
        os.makedirs(dir)


def pip_install(*args):
    return check_call(('pip', 'install') + args)


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
rmtree(BUILD)

with further_output('Downloading dependencies'):
    mkdir(PKGS)
    pip_install(
        '--no-use-wheel', '--download', PKGS,
        '--src', CHECKOUT, '--exists-action', 'w',
        '-r', 'requirements.txt')
    rmtree(CHECKOUT)

with further_output('Unpacking packages'):
    mkdir(SRC)
    for package in glob(PKGS + '/*') + ['.']:
        pip_install('--target', SRC, '--no-compile', '--no-deps', package)

# Get rid of the packaging junk
for dir in glob(SRC + '/*.egg-info'):
    rmtree(dir)

with progress('Creating .pyz zip archive from the sources'):
    with ZipFile(TOOL_PYZ, mode='w', compression=ZIP_DEFLATED) as zip:
        # add the entry point
        zip.write('__main__.py')
        # add python sources
        for realroot, dirs, files in os.walk(SRC):
            ziproot = os.path.relpath(realroot, SRC)
            for file_name in files:
                if file_name.endswith('.py'):
                    zip.write(
                        os.path.join(realroot, file_name),
                        os.path.join(ziproot, file_name))


def make_tool(tool_file_name, runner):
    with open(tool_file_name, 'wb') as f:
        f.write(runner)
        with open(TOOL_PYZ, 'rb') as pyz:
            f.write(pyz.read())

with progress('Creating unix tool'):
    UNIX_RUNNER = b'#!/usr/bin/env python\n'

    make_tool(UNIX_TOOL, UNIX_RUNNER)
    make_executable(UNIX_TOOL)

with progress('Creating windows tool'):
    WINDOWS_RUNNER = b'\r\n'.join((
        b'@echo off',
        b'python.exe "%~f0" %*',
        b'exit /b %errorlevel%',
        b''))

    make_tool(WIN_TOOL, WINDOWS_RUNNER)

print('Done.')
