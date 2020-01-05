import os
import subprocess
import tempfile
import webbrowser

from bead import tech
from bead.box import UnionBox

from ..common import OPTIONAL_ENV
from ..cmdparse import Command
from .csv import read_beads, write_beads
from .sketch import Sketch
from . import sketch as web_sketch
from .dummy import Dummy


class CmdGraph(Command):
    '''
    Visualize connections to other beads.

    Write a GraphViz .dot file and create other representations as requested.
    '''

    def declare(self, arg):
        arg(OPTIONAL_ENV)
        arg('output_base', default='web', nargs='?',
            help='File name base of generated files'
            + ' (e.g. dot file will be stored as <OUTPUT_BASE>.dot)')
        arg('--from-meta', metavar='INPUT_BASE',
            help='Load bead metadata from <INPUT_BASE>.bead-meta')
        arg('--svg', default=False, action='store_true',
            help="Call GraphViz's `dot` to create <OUTPUT_BASE>.svg file as well")
        arg('--png', default=False, action='store_true',
            help="Call GraphViz's `dot` to create an <OUTPUT_BASE>.png file as well")
        arg('--heads-only', default=False, action='store_true',
            help="Show only input edges for the most recent beads for each bead-group")
        arg('names', metavar='NAME', nargs='*',
            help="Restrict output graph to these names and their inputs (default: all beads)")

    def run(self, args):
        output_file_base = args.output_base

        if args.from_meta:
            all_beads = read_beads(f'{args.from_meta}.bead-meta')
        else:
            env = args.get_env()
            all_beads = [Dummy.from_bead(b) for b in load_all_beads(env.get_boxes())]
        print(f"Loaded {len(all_beads)} beads")

        sketch = Sketch.from_beads(all_beads)
        if args.names:
            sketch = web_sketch.set_sinks(sketch, args.names)
        if args.heads_only:
            sketch = web_sketch.heads_of(sketch)
        sketch.color_beads()
        dot_str = sketch.as_dot()

        dot_file = f'{output_file_base}.dot'
        print(f"Creating {dot_file}")
        tech.fs.write_file(dot_file, dot_str)

        if args.png:
            png_file = f'{output_file_base}.png'
            print(f"Creating {png_file}")
            graphviz_dot(dot_file, png_file)

        if args.svg:
            svg_file = f'{output_file_base}.svg'
            print(f"Creating {svg_file}")
            graphviz_dot(dot_file, svg_file)


class CmdView(Command):
    '''
    Visualize connections between archives, clean up all temporary files on exit.
    '''

    def declare(self, arg):
        arg(OPTIONAL_ENV)
        arg('--from-meta', metavar='INPUT_BASE',
            help='Load bead metadata from <INPUT_BASE>-beads.csv and <INPUT_BASE>-inputs.csv')
        arg('--heads-only', default=False, action='store_true',
            help="Show only input edges for the most recent beads for each bead-group")
        arg('names', metavar='NAME', nargs='*',
            help="Restrict output graph to these names and their inputs (default: all beads)")

    def run(self, args):
        tempdir = tech.fs.Path(tempfile.mkdtemp())
        output_file_base = tempdir / 'web'

        if args.from_meta:
            all_beads = read_beads(args.from_meta)
        else:
            env = args.get_env()
            all_beads = [Dummy.from_bead(b) for b in load_all_beads(env.get_boxes())]
        print(f"Loaded {len(all_beads)} beads")

        sketch = Sketch.from_beads(all_beads)
        if args.names:
            sketch = web_sketch.set_sinks(sketch, args.names)
        if args.heads_only:
            sketch = web_sketch.heads_of(sketch)
        sketch.color_beads()
        dot_str = sketch.as_dot()

        dot_file = f'{output_file_base}.dot'
        print(f"Creating {dot_file}")
        tech.fs.write_file(dot_file, dot_str)

        svg_file = f'{output_file_base}.svg'
        print(f"Creating {svg_file}")
        graphviz_dot(dot_file, svg_file)
        print(f"Viewing {svg_file}")
        webbrowser.open(svg_file)

        input('Press return to clean up')
        tech.fs.rmtree(tempdir)


class CmdExport(Command):
    '''
    Export connections to other beads.

    Write bead meta data to file: <OUTPUT_BASE>.bead-meta
    '''

    def declare(self, arg):
        arg(OPTIONAL_ENV)
        arg('output_base', default='web', nargs='?',
            help='File name base, bead meta-s will be written to <OUTPUT_BASE>.bead-meta')

    def run(self, args):
        output_file_name = f'{args.output_base}.bead-meta'

        env = args.get_env()
        all_beads = [Dummy.from_bead(b) for b in load_all_beads(env.get_boxes())]
        print(f"Loaded {len(all_beads)} beads")

        write_beads(output_file_name, all_beads)


class CmdAdvise(Command):
    '''
    Create a script to fix the input map for ARCHIVE.
    '''


def load_all_beads(boxes):
    columns = int(os.environ.get('COLUMNS', 80))
    all_beads = []
    import time
    load_start = time.perf_counter()
    # This UnionBox.all_beads is the meat, the rest is just user feedback for big/slow
    # environments
    for n, bead in enumerate(UnionBox(boxes).all_beads()):
        load_end = time.perf_counter()

        msg = f"\rLoaded bead {n+1} ({bead.archive_filename})"[:columns]
        msg = msg + ' ' * (columns - len(msg))
        print(msg, end="", flush=True)
        if load_end - load_start > 1:
            print(f"\nLoading took {load_end - load_start} seconds")
        all_beads.append(bead)
        load_start = time.perf_counter()
    print("\r" + " " * columns + "\r", end="")
    return all_beads


def graphviz_dot(dot_file, output_file):
    _, ext = os.path.splitext(output_file)
    filetype = ext.lstrip('.')
    cmd = ['dot', dot_file, '-o', output_file, '-T', filetype]
    subprocess.check_call(cmd)
