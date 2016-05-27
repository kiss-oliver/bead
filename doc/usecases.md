# Use case narratives:

## Initial setup

    $ mkdir /somepath/BeadBox
    $ bead box add main /somepath/BeadBox
    Will remember box main

## Create an empty BEAD with name `name`

    /somepath$ bead new name
    Created name
    
    /somepath$ cd name/
    /somepath/name$ echo World > output/name
    
    /somepath/name$ bead save
    Successfully stored bead.
    
    /somepath/name$ bead nuke
    Deleted workspace /somepath/name

## Create a new data package, linking to existing inputs

    /somepath$ bead new hello
    Created hello
    /somepath$ cd hello/

Add data from another bead at `input/<input-name>/`

    /somepath/hello$ bead input add name name
    name loaded on name.

Create a program `greet` that produces a greeting:

    /somepath/hello$ cat > greet <<-'EOF'
    read name < input/name/name
    echo "Hello $name!" > output/greeting
    EOF

Run the program:

    /somepath/hello$ bash greet 

Verify output:

    /somepath/hello$ cat output/greeting
    Hello World!


## Package the data and send to an outside collaborator

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
