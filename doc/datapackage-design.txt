# Requirements

- as simple as possible
- one package - one team - distributed work
- should be possible to work offline - without access to network
- packages can be integrated from multiple sources and verified that indeed they are steps of a data flow
- reproducibility must be verifiable (those which are not reproducible are marked, a final result is reproducible if all packages it depends on are reproducible)
- cross-platform access (Win-Mac-Lin)
- create a new package based on an older one by updating its input
    - track input channels
    - do it automatically?!
- access control with granularity of package-uuid - restricted packages


# Assumptions

- code is small relative to data
- python app is OK


# Roles

- package developer
- package data user


# Use cases

- developer:
    + create new package layout - with directory structure
    + unpack existing pkg for development (w/ most recent input data)
    + manage input data
        + get input data (name, channel, version, nick)
            * extract data under input/<nick>
            * register (name-uuid, version-uuid, nick) in metadata
        + delete input data
        + rename input data (nick)
        + upgrade input data (nick[, version-uuid])
    + create package from directory
        * create archive
    + publish package on a repository (optionally with all its dependencies)
        + make package available on a channel
    + export package from a repository as an archive

- data user:
    + get data
    ? get data as okfn datapackage

# Datapackage

A datapackage is an immutable archive with annotation.

## Archive

The archive contains

- data
- code
- meta:
    + ordering: time stamp
    + catalog:
        + package name (package-uuid)
        + update channel information (channel-uuid)
	+ how to reproduce:
	    + references to input data packages (name, version, nick)
	    + how to run the code

### Storage standards

- bagit (data integrity with md5, sha1 sums)
- okfn datapackage (metadata & generic tools)

## Annotations

### Immutable

Immutable annotations can be encoded in the file name.

- name
- version
    - channel
    - ordering info (sequence or time stamp?)
    - crypto-hash of package (md5/sha1)

### Volatile

- description
- developer info
- flags ("reproduced")
- tags ("exhibit-20140000-1", "test")


# Repository

A repository is maintaining a collection of packages.
A repository is a realm, in that packages get some immutable annotation when they arrive into the repository.

new packages can be deposited in
existing packages can be retrieved by (name, version)
provides ordering of packages in buckets:
    (name, channel) -> ordered list of versions

- must be easy to set up - one or more by developers?, one per project?
- must be cross-platform (Win-Mac-Lin)
- may provide remote access
- must have local (offline) mode
- the same package can be stored again under different name, channel
- must ensure integrity of packages
- should be easy to incrementally back up
- may provide tools to discover and remove unused or unreproducible packages


# Version problems

Are avoided by

- sequence number is assigned by the repo (package realm)
- same package can have multiple versions, even within same repo
- same package can be present in different channels
- packages are unambiguously referenced by (name, channel, crypto-hash)
- channels are used for differentiating incompatible streams under the same name

Storage:
- http://en.wikipedia.org/wiki/Content-addressable_storage
- git? http://git-scm.com/book/en/Git-Internals-Git-Objects

# open problems:

- how to handle conflicts (same version released twice)

    - use realms that are repository specific
    - versions are realm specific

- how to configure repos

    XXX-config <repo> <cache>

- how do releasing work?

    XXX-release [<channel>]

- security: restricted package access

    - Encrypt packages?
    - apply unix permissions on parts of a repo?
