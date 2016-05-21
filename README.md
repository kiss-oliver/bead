[![Build Status](https://travis-ci.org/e3krisztian/bead.svg?branch=master)](https://travis-ci.org/e3krisztian/bead)

    B-E-+
     \ \ \
      +-A-D

# BEAD


BEAD is a format for freezing and storing computations while `bead` is a tool that helps
capturing and managing computations in BEAD formats.


## Concept

Given a discrete computation of the form

    output = function(*inputs)

a BEAD captures all three named parts:

- `output` is the result of the computation - data, it is contained verbatim
- `function` is a code that computes `output` from the `inputs`
- `inputs` are stored as references to other BEADs - they are the `output` part of
  computations

It also has some other metadata - e.g. a unique identifier that is supposed to be common 
between different versions (either part is updated) of the same computation and a timestamp
when it was frozen.


## Status

### bead as a tool *is not production ready, yet!*

Although most of the important stuff is implemented, the metadata format is still not fixed,
which might render every existing BEAD incompatible after the change.

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

Updated by script ([./ci](https://github.com/e3krisztian/bead/blob/master/ci)), text in this section and afterwards will be overwritten

- [FIXME: Box.find_beads dies on non bead in the directory](https://github.com/e3krisztian/bead/blob/master/bead/box.py#L137)
- [FIXME: Box.find_names dies on non bead in the directory](https://github.com/e3krisztian/bead/blob/master/bead/box.py#L165)
- [FIXME: die with message when directory already exists](https://github.com/e3krisztian/bead/blob/master/bead_cli/workspace.py#L49)
- [FIXME: robot: environment file should be built by a function in environment](https://github.com/e3krisztian/bead/blob/master/bead_cli/test_robot.py#L36)
- [FIXME: update: fix to allow to select previous/next/closest to a timestamp bead](https://github.com/e3krisztian/bead/blob/master/bead_cli/input.py#L125)
- [TODO: add tests for timestamps, parse_iso8601, parse_timedelta](https://github.com/e3krisztian/bead/blob/master/bead/tech/timestamp.py#L232)
- [TODO: Box: support user maintained directory hierarchy](https://github.com/e3krisztian/bead/blob/master/bead/box.py#L99)
- [TODO: calculate and add index parameter (--next, --prev)](https://github.com/e3krisztian/bead/blob/master/bead_cli/common.py#L215)
- [TODO: implement more options](https://github.com/e3krisztian/bead/blob/master/bead_cli/common.py#L118)
- [TODO: support shortened content hashes](https://github.com/e3krisztian/bead/blob/master/bead/spec.py#L19)
- [TODO: use a template and render it with passing in all data](https://github.com/e3krisztian/bead/blob/master/bead_cli/workspace.py#L220)
- [XXX: cli parsing: revisit when python 2.x no longer supported](https://github.com/e3krisztian/bead/blob/master/bead_cli/cmdparse.py#L86)
- [XXX: directory itself might be a pattern - is it OK?](https://github.com/e3krisztian/bead/blob/master/bead/box.py#L135)
- [XXX: heapq might be faster a bit?](https://github.com/e3krisztian/bead/blob/master/bead/box.py#L57)
- [XXX: introspect parameter names, default values, annotations?](https://github.com/e3krisztian/bead/blob/master/bead_cli/cmdparse.py#L121)
- [XXX: list command: use tabulate?](https://github.com/e3krisztian/bead/blob/master/bead_cli/box.py#L60)
- [XXX: order_and_limit_beads is called twice - first in find_beads](https://github.com/e3krisztian/bead/blob/master/bead_cli/common.py#L195)
- [XXX: try to load smaller inputs?](https://github.com/e3krisztian/bead/blob/master/bead_cli/workspace.py#L149)
