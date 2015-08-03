[![Build Status](https://travis-ci.org/krisztianfekete/lib.svg?branch=master)](https://travis-ci.org/krisztianfekete/lib)

lib will be a data package manager, it is in the planning phase, with some bits implemented for demo purposes.
It will be renamed, its license changed, its internal working modified backward incompatibly, ....

Do not use it yet!

Install instructions (for the curious)
--------------------------------------

Run the `build.py` tool to create the `ws` tool.

There is an alternative, which works but used only for automated testing with `travis`/`tox`:

```
# create a virtualenv, enter it
mktmpenv; cd -
pip install -r requirements.txt .
# now you should have a new tool named ws:
ws -h
```
