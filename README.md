[![Build Status](https://travis-ci.org/krisztianfekete/lib.svg?branch=master)](https://travis-ci.org/krisztianfekete/lib)

**`lib`** will be a data package manager, it is in the early testing phase, with most important stuff implemented for demo/testing purposes.

It will be renamed, its internal working modified backward incompatibly, ....

Documentation is non-existent at this point - except for command line help.

It is definitely sharp on the edges - **do not use it for production, yet!**


Install instructions
--------------------

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
