import argparse
import os
import subprocess
import tempfile
import webbrowser

from bead import tech
from bead.box import UnionBox

from ..common import OPTIONAL_ENV, die
from ..cmdparse import Command
from .io import read_beads, write_beads
from .sketch import Sketch
from . import sketch as web_sketch
from .dummy import Dummy


class CmdWeb(Command):
    '''
    Visualize the big picture.

    Tool to capture/load/filter/save/visualize connections between
    all available beads.

    Sub-commands describe a processing pipe-line, where each sub command
    work on an input graph, and yield an output graph.  Where the graph
    is defined by archive meta-s as nodes and input connections between
    archive meta-s as edges.

    The processing pipe-line starts off with all the available beads in
    the defined boxes as initial input.

    However preparing this big picture is an expensive operation if there
    are more than a dozen beads, therefore it is optimized away if the
    first sub-command is "load".

    Sub commands simplify the big picture by dropping input connections
    and meta-s.

    Subcommands:

    load filename.web
        Load previously exported web metadata from file.

    / [source-name[s]] ... [sink-name[s]] /
        Filters beads by input connections:
        - if the set of sources is not empty:
          drop all that do not have any of the sources as direct/indirect
          inputs.
        - if the set of sinks is not empty:
          drop all that are not direct/indirect inputs to any of the sinks.

    save filename.{web,dot,png,svg}
        Save current web metadata to file - for processing later.

    color
        Assign freshness of beads.
        Answers the question: "Are all input at the latest version?"

    heads
        Reduce connections to include only most recent versions
        and beads to only those most recent and those referenced
        by the remaining connections.
    '''

    FORMATTER_CLASS = argparse.RawDescriptionHelpFormatter

    def declare(self, arg):
        arg(OPTIONAL_ENV)
        arg(
            'words',
            metavar='...',
            nargs=argparse.REMAINDER,
            help='Sub-commands and their arguments'
        )

    def run(self, args):
        env = args.get_env()
        commands, remaining_words = parse_commands(env, args.words)
        if remaining_words:
            msg = 'Could not fully parse command line.\n'
            if commands:
                msg += 'Parsed commands:'
                msg += '\n\t'.join(map(str, commands))
            msg += f'\nCould not parse: {remaining_words}'
            die(msg)
        else:
            sketch = Sketch.from_beads([])
            for command in commands:
                sketch = command(sketch)


def parse_commands(env, words):
    remaining_words = words[::-1]
    commands = []

    if remaining_words and remaining_words[-1] != 'load':
        commands.append(LoadAll(env.get_boxes()))

    while remaining_words:
        remaining = remaining_words[:]
        cmd_name = remaining_words.pop()
        try:
            cmd_class = SUBCOMMANDS[cmd_name]
            cmd = cmd_class(remaining_words)
        except:
            return commands, remaining
        commands.append(cmd)

    return commands, remaining_words[::-1]


class SketchProcessor:
    def __init__(self, _args):
        pass

    def __call__(self, sketch):
        return sketch

    def __str__(self):
        cls = self.__class__.__name__
        args = vars(self)
        return f'{cls}({args})'

    def sketch_from_beads(self, beads):
        return Sketch.from_beads([Dummy.from_bead(bead) for bead in beads])


class LoadAll(SketchProcessor):
    def __init__(self, boxes):
        super().__init__([])
        self.boxes = boxes

    def __call__(self, _sketch):
        beads = load_all_beads(self.boxes)
        return self.sketch_from_beads(beads)


class Load(SketchProcessor):
    def __init__(self, args):
        self.file_name = args.pop()

    def __call__(self, _sketch):
        beads = read_beads(self.file_name)
        return self.sketch_from_beads(beads)


class Save(SketchProcessor):
    def __init__(self, args):
        self.file_name = args.pop()

    def __call__(self, sketch):
        return write_beads(self.file_name, sketch.beads)


class Filter(SketchProcessor):
    def __init__(self, args):
        self.sources = self._pop_names(args, sentinel='...')
        self.sinks = self._pop_names(args, sentinel='/')
        super().__init__(args)

    def _pop_names(self, args, sentinel):
        names = []
        while args:
            name = args.pop()
            if name == sentinel:
                return names
            if name in ('...', '/'):
                raise ValueError(f'Unexpected delimiter: {repr(name)} after {names}.')
            if not is_valid_name(name):
                raise ValueError(f'Malformed name: {repr(name)} after {names}.')
            names.append(name)
        raise ValueError(f'Delimiter not found: {repr(sentinel)}.')

    def __call__(self, _env, _sketch):
        print(f'filter: {self.sources} ... {self.sinks}')


def is_valid_name(name):
    return name not in ('...', '/')


SUBCOMMANDS = {
    'load': Load,
    'save': Save,
    '/': Filter,
}


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
