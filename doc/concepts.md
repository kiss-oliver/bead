# Concepts

## Workspace

Prototype of a BEAD.
A directory, where the user works.
At some time is supposed to have all the inputs, the code and the output of a computation.

It is a directory with some special content, so it must be created via the bead tool:
- there are metadata in a hidden .bead-meta directory
- there are 3 standard directories, that has special meanings:
  - input - where input data is read from, it is read only, managed by the `bead` tool
  - temp - temporary outputs, this is an area that is ignored when freezing the computation
  - output - this is where results of the computation go


## BEAD

Is a frozen, discrete computation.
Created from a Workspace.
It is currently a zip file for convenience.

A BEAD is intended to capture data with the code that produced it.
The goal is transparency and semi-automatic reproducability through extra tooling.
Full automatic reproducability is assumed to be inpractical/expensive, 
however it can be achieved by gradual process/quality improvements (learning through feedback).

The BEAD format is designed to be
- resilient to change
- decentralized
- keep enough information to be able to get both the details and the big picture (if all relevant BEADs are available)

The main technology involved is a combination of different probabilistic identifiers (UUID, secure hash, Merkle-tree).

Main BEAD properties:
- bead_uuid that is shared with other versions of a BEAD (book analogy: ISSN)
- a content_hash, that is unique for every BEAD (~version, book analogy: ISBN)
 - it is calculated, so changes in a BEAD makes it either invalid or a new version
- freeze time (for ordering versions, this is fragile in theory as depends on correctly set clocks, but in practice it is expected to cause few problems)
- freeze name
- references to its inputs (bead_uuid, content_hash)


## Box

This is where BEADs are saved to and loaded from.
Also give names to BEADs and provide search.

The current naive implementation is a flat directory on the file system.



