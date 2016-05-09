[![Build Status](https://travis-ci.org/e3krisztian/bead.svg?branch=master)](https://travis-ci.org/e3krisztian/bead)

    b-e-+
     \ \ \
      +-a-d

# bead


**`bead`** is both a format for freezing and storing computations and a tool that helps 
capturing and managing computations in `bead` formats.


## bead as a concept

Given a computation of the form

    output = function(*inputs)

a `bead` contains all three named parts:

- `output` is the result of the computation - data, it is contained verbatim
- `function` is a code that computes `output` from the `inputs`
- `inputs` are stored as references to other `bead`s - they are the `output` of other 
calculations

It also has some other metadata - e.g. a unique identifier that is supposed to be common 
between different versions (either part is updated) of the same computation and a timestamp
when it was frozen.


## bead as a tool *is not production ready, yet!*

Although most of the important stuff is implemented, some important names will change in the
metadata (to get names right), which will render every existing bead incompatible after the 
change.

Documentation for the tool is non-existent at this point - except for command line help.
The doc directory currently contains design fragments - you will be mislead by them as they 
are nor describing the current situations nor are they showing the future.


## Install instructions

Ensure you have Python installed.

Run the `build.py` script to create the `bead` tool:

```
$ python build.py
```

This generates one-file executables for unix, mac, and windows in the `build` directory:
- `bead` unix & mac
- `bead.cmd` windows

Move/copy the `bead` binary for your platform to some directory on your `PATH`.

E.g.

```
$ cp build/bead ~/.local/bin
```

If you test it, please give [feedback](../../issues) on
- general usability
- misleading/unclear help (currently: command line help)
- what is missing (I know about documentation)
- what is not working as you would expect

Any other nuisance reported - however minor you think it be - is important and welcome!

Thank you for your interest!


## TODOs

Updated by script, text in this section and afterwards will be overwritten

- [# XXX revisit when python 2.x no longer supported](https://github.com/e3krisztian/bead/blob/renames/bead/commands/cmdparse.py#L84)
- [# XXX: introspect parameter names, default values, annotations?](https://github.com/e3krisztian/bead/blob/renames/bead/commands/cmdparse.py#L119)
- [# TODO: implement more options](https://github.com/e3krisztian/bead/blob/renames/bead/commands/common.py#L82)
- [# XXX order_and_limit_packages is called twice - first in find_packages](https://github.com/e3krisztian/bead/blob/renames/bead/commands/common.py#L140)
- [# TODO: calculate and add index parameter (--next, --prev)](https://github.com/e3krisztian/bead/blob/renames/bead/commands/common.py#L160)
- [# FIXME: update: fix to allow to select previous/next/closest to a timestamp package](https://github.com/e3krisztian/bead/blob/renames/bead/commands/input.py#L126)
- [# FIXME: input._update](https://github.com/e3krisztian/bead/blob/renames/bead/commands/input.py#L137)
- [# XXX use tabulate?](https://github.com/e3krisztian/bead/blob/renames/bead/commands/repo.py#L53)
- [# FIXME: die with message when directory already exists](https://github.com/e3krisztian/bead/blob/renames/bead/commands/workspace.py#L50)
- [# TODO: delete arg_metavar.BEAD_REF](https://github.com/e3krisztian/bead/blob/renames/bead/commands/workspace.py#L119)
- [# XXX: try to load smaller inputs?](https://github.com/e3krisztian/bead/blob/renames/bead/commands/workspace.py#L147)
- [# TODO: use a template and render it with passing in all data](https://github.com/e3krisztian/bead/blob/renames/bead/commands/workspace.py#L216)
- [# FIXME: rename `package` to `bead_uuid`](https://github.com/e3krisztian/bead/blob/renames/bead/pkg/meta.py#L44)
- [# FIXME: uuid -> bead_uuid](https://github.com/e3krisztian/bead/blob/renames/bead/pkg/package.py#L12)
- [# XXX - is there any practical use for this?](https://github.com/e3krisztian/bead/blob/renames/bead/pkg/spec.py#L12)
- [# TODO: support shortened content hashes](https://github.com/e3krisztian/bead/blob/renames/bead/pkg/spec.py#L21)
- [# FIXME: add zip comment with pointers to this software](https://github.com/e3krisztian/bead/blob/renames/bead/pkg/workspace.py#L187)
- [# FIXME: create environment module](https://github.com/e3krisztian/bead/blob/renames/bead/repos.py#L25)
- [# XXX: heapq might be faster a bit?](https://github.com/e3krisztian/bead/blob/renames/bead/repos.py#L109)
- [# TODO: user maintained directory hierarchy](https://github.com/e3krisztian/bead/blob/renames/bead/repos.py#L123)
- [# XXX: directory itself might be a pattern - is it OK?](https://github.com/e3krisztian/bead/blob/renames/bead/repos.py#L159)
- [# FIXME: Repository.find_packages dies on non package in the directory](https://github.com/e3krisztian/bead/blob/renames/bead/repos.py#L161)
- [# FIXME: Repository.find_names dies on non package in the directory](https://github.com/e3krisztian/bead/blob/renames/bead/repos.py#L190)
- [# FIXME: move get_bead to Environment.get_bead](https://github.com/e3krisztian/bead/blob/renames/bead/repos.py#L258)
- [# TODO: add tests for timestamps, parse_iso8601, parse_timedelta](https://github.com/e3krisztian/bead/blob/renames/bead/tech/timestamp.py#L232)
- [assert False, 'FIXME: no direct tests for new'](https://github.com/e3krisztian/bead/blob/renames/bead/test_cli/test_new_command.py#L13)
