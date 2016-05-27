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



# Use case narratives:

0. Initial setup:

    $ mkdir /somepath/BeadBox
    $ bead box add main /somepath/BeadBox
    Will remember box main

    # create a BEAD with name `name`, that will have 
    # no input, no code and a single output file 'name' with some name

    /somepath$ bead new name
    Created name

    /somepath$ cd name/
    /somepath/name$ echo World > output/name

    /somepath/name$ bead save
    Successfully stored bead.

    /somepath/name$ bead nuke
    Deleted workspace /somepath/name



A. this is how you create a new data package, linking to existing inputs.

    /somepath$ bead new hello
    Created hello
    /somepath$ cd hello/

    # add data from another bead at input/<input-name>/

    /somepath/hello$ bead input add name name
    name loaded on name.

    # create program `greet` that creates a greeting

    /somepath/hello$ cat > greet <<-'EOF'
    read name < input/name/name
    echo "Hello $name!" > output/greeting
    EOF

    # run the program

    /somepath/hello$ bash greet 

    # observe output

    /somepath/hello$ cat output/greeting
    Hello World!


B. this is how you package the data and send to an outside collaborator.

    # assume we are just after A.
    
    # save the greeting

    /somepath/hello$ bead save
    Successfully stored bead.

    # now the content of /somepath/BeadBox is

    /somepath$ ls -1 BeadBox/
    hello_20160527T130218513418+0200.zip
    name_20160527T113419427017+0200.zip

    # which are (in this case small) normal zip files, which can be 
    # transferred by any means (e.g. emailed) to someone who needs it
    # she can either process it via the bead tool to keep the integrity
    # of provenance information, or in the worst case access the data
    # by directly unzipping relevant bits from the zip file

    # Workspace's output/* is saved under data/*

    /somepath$ unzip -p BeadBox/hello_20160527T130218513418+0200.zip data/greeting
    Hello World!

    /somepath$ unzip -v BeadBox/hello_20160527T130218513418+0200.zip 
    Archive:  BeadBox/hello_20160527T130218513418+0200.zip

    This file is a BEAD zip archive.

    It is a normal zip file that stores a discrete computation of the form

        output = code(*inputs)

    The archive contains

    - inputs as part of metadata file: references (content hash) to other BEADs
    - code   as files
    - output as files
    - extra metadata to support
      - linking different versions of the same computation
      - determining the newest version
      - reproducing multi-BEAD computation sequences built by a distributed team

    There {is,will be,was} more info about BEADs at

    - https://unknot.io
    - https://github.com/ceumicrodata/bead
    - https://github.com/e3krisztian/bead

    ----

     Length   Method    Size  Cmpr    Date    Time   CRC-32   Name
    --------  ------  ------- ---- ---------- ----- --------  ----
          13  Defl:N       15 -15% 2016-05-27 13:01 7d14dddd  data/greeting
          66  Defl:N       58  12% 2016-05-27 13:01 753b9d15  code/greet
         742  Defl:N      378  49% 2016-05-27 13:02 a4eb5de9  meta/bead
         456  Defl:N      281  38% 2016-05-27 13:02 9a206f53  meta/checksums
    --------          -------  ---                            -------
        1277              732  43%                            4 files
