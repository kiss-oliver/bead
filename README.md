[![Build Status](https://travis-ci.org/e3krisztian/lib.svg?branch=master)](https://travis-ci.org/e3krisztian/lib)

**`lib`** will be a data package manager, it is in the early testing phase, with most important stuff implemented for demo/testing purposes.

It will be renamed (to *bead*), its internal working modified backward incompatibly (metadata key names are to change!), ....

Documentation is non-existent at this point - except for command line help.

It is definitely sharp on the edges - **do not use it for production, yet!**


## Install instructions

Run the `build.py` tool to create the `ws` tool:

```
$ python build.py
```

This generates one-file executables for major platforms in the `build` directory:
- `ws` unix & mac
- `ws.cmd` windows

Move/copy the `ws` binary for your platform to some directory on your `PATH`.

```
$ cp build/ws ~/.local/bin
```

Note: the name `ws` comes from *workspace*, it might change in the future.

If you test it, please give [feedback](../../issues) on
- general usability
- misleading/unclear help
- what is missing
- what is not working as you would expect
- any other nuisance - however minor you think it be - is important and welcome!

Thank you for your interest!


## TODOs

Updated by script, text will be overwritten after this section

- [# XXX revisit when python 2.x no longer supported](https://github.com/e3krisztian/lib/blob/master/lib/commands/cmdparse.py#L84)
- [# XXX: introspect parameter names, default values, annotations?](https://github.com/e3krisztian/lib/blob/master/lib/commands/cmdparse.py#L119)
- [# TODO: implement more options](https://github.com/e3krisztian/lib/blob/master/lib/commands/common.py#L82)
- [# XXX order_and_limit_packages is called twice - first in find_packages](https://github.com/e3krisztian/lib/blob/master/lib/commands/common.py#L140)
- [# TODO: calculate and add index parameter (--next, --prev)](https://github.com/e3krisztian/lib/blob/master/lib/commands/common.py#L160)
- [# FIXME: update: fix to allow to select previous/next/closest to a timestamp package](https://github.com/e3krisztian/lib/blob/master/lib/commands/input.py#L126)
- [# FIXME: input._update](https://github.com/e3krisztian/lib/blob/master/lib/commands/input.py#L137)
- [# XXX use tabulate?](https://github.com/e3krisztian/lib/blob/master/lib/commands/repo.py#L53)
- [# FIXME: die with message when directory already exists](https://github.com/e3krisztian/lib/blob/master/lib/commands/workspace.py#L49)
- [# TODO: delete arg_metavar.PACKAGE_REF, arg_help.PACKAGE_REF](https://github.com/e3krisztian/lib/blob/master/lib/commands/workspace.py#L118)
- [# XXX: try to load smaller inputs?](https://github.com/e3krisztian/lib/blob/master/lib/commands/workspace.py#L146)
- [# FIXME workspace.get_package_name](https://github.com/e3krisztian/lib/blob/master/lib/commands/workspace.py#L167)
- [# TODO: use a template and render it with passing in all data](https://github.com/e3krisztian/lib/blob/master/lib/commands/workspace.py#L262)
- [# FIXME: workspace.status](https://github.com/e3krisztian/lib/blob/master/lib/commands/workspace.py#L266)
- [# FIXME: rename `version` to `content-hash`](https://github.com/e3krisztian/lib/blob/master/lib/pkg/meta.py#L41)
- [# FIXME: version -> content_hash](https://github.com/e3krisztian/lib/blob/master/lib/pkg/package.py#L13)
- [# XXX - is there any practical use for this?](https://github.com/e3krisztian/lib/blob/master/lib/pkg/spec.py#L12)
- [# TODO: support shortened content hashes](https://github.com/e3krisztian/lib/blob/master/lib/pkg/spec.py#L21)
- [# FIXME: add zip comment with pointers to this software](https://github.com/e3krisztian/lib/blob/master/lib/pkg/workspace.py#L187)
- [# FIXME: create environment module](https://github.com/e3krisztian/lib/blob/master/lib/repos.py#L23)
- [# XXX: heapq might be faster a bit?](https://github.com/e3krisztian/lib/blob/master/lib/repos.py#L107)
- [# TODO: user maintained directory hierarchy](https://github.com/e3krisztian/lib/blob/master/lib/repos.py#L121)
- [# XXX: directory itself might be a pattern - is it OK?](https://github.com/e3krisztian/lib/blob/master/lib/repos.py#L157)
- [# FIXME: move get_package to Environment.get_package](https://github.com/e3krisztian/lib/blob/master/lib/repos.py#L218)
- [# TODO: add tests for timestamps, parse_iso8601, parse_timedelta](https://github.com/e3krisztian/lib/blob/master/lib/tech/timestamp.py#L232)
- [assert False, 'FIXME: no direct tests for new'](https://github.com/e3krisztian/lib/blob/master/lib/test_cli/test_new_command.py#L13)
