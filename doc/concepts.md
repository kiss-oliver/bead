# Concepts

Data packages can be in one of two states. Under active development in a `workspace`, or packaged and stored as a `bead`. Beads are stored in a `box`, which is just a collection of completed beads.

![Workflows](https://raw.githubusercontent.com/ceumicrodata/bead/master/doc/workflows.png)

To see how workspaces are created from beads and vice versa, also see https://github.com/ceumicrodata/bead/blob/master/doc/usecases.md

## Workspace

The `workspace` contains a prototype of a bead, computation under active development. This is a directory, where the user works. At some time is supposed to have all the inputs, the code and the output of a computation.

The directory has special structure and content, so it must be created via the `bead` tool:
- there are metadata in a hidden .bead-meta directory
- there are 3 standard directories with special meanings:
  - input: where input data is read from. It is read only, managed by the `bead` tool.
  - temp: temporary outputs, this is an area that is ignored when saving the bead.
  - output: This is where results of the computation are stored.

## bead

A `bead` is a frozen, discrete computation, created from a `workspace`. It is stored as a zip file for convenience.

A bead is intended to capture data with the code that produced it. The goal is transparency and semi-automatic reproducability through extra tooling. Full automatic reproducability is assumed to be inpractical/expensive, however it can be achieved by gradual process/quality improvements (learning through feedback).

The bead format is designed to be
- resilient to change
- decentralized
- keep enough information to be able to get both the details and the big picture (if all relevant beads are available)

The main technology involved is a combination of different probabilistic identifiers (UUID, secure hash, Merkle-tree).

Main bead properties:
- bead_uuid that is shared with other versions of a bead (book analogy: ISSN)
- a content_hash, that is unique for every bead (~version, book analogy: ISBN)
 - it is calculated, so changes in a bead makes it either invalid or a new version
- freeze time (for ordering versions, this is fragile in theory as depends on correctly set clocks, but in practice it is expected to cause few problems)
- freeze name
- references to its inputs (bead_uuid, content_hash)

## Box

A `box` is where beads are saved to and loaded from. It also gives names to beads and provide minimal search functionality. Currently, boxes are implemented a flat directories on the file system.



