import os

from bead import tech
from bead.archive import Archive
from .cmdparse import Command
from .common import OPTIONAL_ENV, die
from .web import rewire


class CmdAdd(Command):
    '''
    Define a box.
    '''

    def declare(self, arg):
        arg('name')
        arg('directory')
        arg(OPTIONAL_ENV)

    def run(self, args):
        '''
        Define a box.
        '''
        name, directory = args.name, args.directory
        env = args.get_env()

        if not os.path.isdir(directory):
            print(f'ERROR: "{directory}" is not an existing directory!')
            return
        location = os.path.abspath(directory)
        try:
            env.add_box(name, location)
            env.save()
            print(f'Will remember box {name}')
        except ValueError as e:
            print('ERROR:', *e.args)
            print('Check the parameters: both name and directory must be unique!')


class CmdList(Command):
    '''
    List boxes.
    '''

    def declare(self, arg):
        arg(OPTIONAL_ENV)

    def run(self, args):
        boxes = args.get_env().get_boxes()

        def print_box(box):
            print(f'{box.name}: {box.location}')
        if boxes:
            print('Boxes:')
            print('-------------')
            for box in boxes:
                print_box(box)
        else:
            print('There are no defined boxes')


class CmdForget(Command):
    '''
    Remove the named box from the boxes known by the tool.
    '''

    def declare(self, arg):
        arg('name')
        arg(OPTIONAL_ENV)

    def run(self, args):
        name = args.name
        env = args.get_env()

        if env.is_known_box(name):
            env.forget_box(name)
            env.save()
            print(f'Box "{name}" is forgotten')
        else:
            print(f'WARNING: no box defined with "{name}"')


class CmdXmeta(Command):
    '''
    eXport eXtended meta attributes to a file next to zip archive.
    '''
    def declare(self, arg):
        arg('zip_archive_filename')

    def run(self, args):
        archive = Archive(args.zip_archive_filename)
        archive.save_cache()
        print(f'Saved {archive.cache_path}')


class CmdRewire(Command):
    '''
    Remap inputs.
    '''
    def declare(self, arg):
        arg('name')
        arg('rewire_options_json')
        arg(OPTIONAL_ENV)

    def run(self, args):
        print('TODO: implement')
        env = args.get_env()
        name = args.name
        for box in env.get_boxes():
            if box.name == name:
                break
        else:
            die(f'Unknown box {name}')
        rewire_options = tech.persistence.file_load(args.rewire_options_json)
        rewire_specs = rewire_options.get(name, [])
        # This could be painfully slow, if there are many beads and their metadata
        # is not exported/cached with xmeta
        for bead in box.all_beads():
            rewire.apply(bead, rewire_specs)
