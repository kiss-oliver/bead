import shutil
import subprocess

from bead.test import skipUnless


def _has_dot():
    if shutil.which('dot') == '/usr/bin/dot':
        try:
            output = subprocess.check_output(['dot', '-V'], stderr=subprocess.STDOUT)
        except subprocess.SubprocessError:
            return False
        return 'graphviz' in output.decode('utf-8').lower()
    return False


HAS_DOT = _has_dot()


def needs_dot(f):
    """
    Decorator to skip tests requiring GraphViz's dot tool.
    """
    return skipUnless(HAS_DOT, "Requires GraphViz's dot tool")(f)
