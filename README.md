Health:
AppVeyor [![Build Status](https://ci.appveyor.com/api/projects/status/github/e3krisztian/bead?branch=master&svg=true)](https://ci.appveyor.com/project/e3krisztian/bead)

[![CI](https://github.com/e3krisztian/bead/actions/workflows/ci.yml/badge.svg)](https://github.com/e3krisztian/bead/actions/workflows/ci.yml)

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

- `output` - *data files* (results of the computation)
- `function` - *source code files*, that when run hopefully compute `output` from `inputs`
- `inputs` - are other BEADs' `output` and thus stored as *references to* those *BEADs*

As a special case pure data can be thought of as *constant computation*
having only output but neither inputs nor source code.

A BEAD has some other metadata - notably it has a `kind` property which is shared by
different versions of the conceptually same computation (input or function may be updated/improved)
and a timestamp when the computation was frozen.

The `kind` and timestamp properties enable a meaningful `update` operation on inputs.

New computations get a new, universally unique `kind` (technically an uuid).


## Status

### Used in production for 2 years now, there are 100+ frozen computations

Although most of the important stuff is implemented, there are still some raw edges.

Documentation for the tool is mostly the command line help.

The `doc` directory has concept descriptions, maybe some use cases,
but there are also design fragments - you might be mislead by them as they
are nor describing the current situations nor are they showing the future.
FIXME: clean up documentation.


## Install instructions

Ensure you have Python 3.6+ installed.

Run `make executables` to create the `bead` tool:

```
$ python build.py
```

This generates one-file executables for unix, mac, and windows in the `executables` directory:
- `bead` unix & mac
- `bead.cmd` windows

Move/copy the `bead` binary for your platform to some directory on your `PATH`.

E.g.

```
$ cp executables/bead ~/.local/bin
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

- [FIXME: this test helper uses private to box implementation information](https://github.com/e3krisztian/bead/blob/master/bead_cli/test_feature_update_by_name.py#L108)
- [TODO: log/report problem](https://github.com/e3krisztian/bead/blob/master/bead/box.py#L160)
- [TODO: remove nuke command after next release](https://github.com/e3krisztian/bead/blob/master/bead_cli/main.py#L62)
- [XXX: try to load smaller inputs?](https://github.com/e3krisztian/bead/blob/master/bead_cli/workspace.py#L161)
- [XXX: (usability) save - support saving directly to a directory outside of workspace](https://github.com/e3krisztian/bead/blob/master/bead_cli/workspace.py#L87)
