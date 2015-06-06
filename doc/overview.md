# The problem

We have a highly distributed analysis workflow, but:
 - can not address data precisely
 - do not have available metadata of dependencies (they are in human heads or at best in README-s)
 - do not have a global and complete overview of the workflow
 - depend on humans to reproduce / fix missing/broken scripts when needed - we do not know when it is needed


# Vision

Tool for transparent data analysis workflow, that is highly distributed.

The tool must help in achieving product reproducibility and doing it in a distributed working style, taking away some of the problems, but restricting almost nothing.

Even partial success is better than either too much restrictions or chaos.

Highly distributed means, that developers are working individually on their part.
There is no user visible global namespace, concrete package files can be renamed arbitrarily.
Developers in the analysis workflow need to access only directly used data packages (they would need those anyway!).

Transparent means, that the code/data layout once looked like the one packaged including its data dependency information.


# Assumptions

- data analysis: code is small relative to data
- python app is OK


# Virtues to achieve (design and implementation guides):

- usable
- small
- simple(?)
- familiar (wherever possible)
- non-restrictive
- resilient
- distributed


# Requirements

- conceptual simplicity
    - package centric view of workflow
    - stores provenance, code and data output
    - peer to peer, but file exchange is outside the core system
    - tamper resistant packages (SHA1 hash as version)
- cross-platform (Win-Mac-Lin)
    - single file executable (might be platform specific)
- support distributed team-work
- data and data-flow centric
- no restrictions other than the minimal directory structure

- usability:
    - must be easy to work with for non-programmers
    - should be hard to make mistakes
    - updates: easily create updated package versions based on new input
- reproducibility must be verifiable (-> further tooling)
- processing sensitive data should be possible
    - access control with granularity of package-uuid - restricted packages
    - packages might be owned, but ownership surely changes over time


# Extensions

Transparency is much weaker than reproducable, but it is on that road: the package can be reproducible if there is no change to the code after the output has been generated.

The final goal of course is reproducability: collecting all the packages created, we can generate the output using only the primary inputs and the metadata in the packages.

Reproducability can be achieved by tooling and feedback (by an automatism - software reproducing agent).

Possible further tooling (third party apps?):
    - export data packages leading to a certain product (= concrete data package version)
        - works with a full dependency graph
    - automatic verification agent: check if there is enough metadata and code to reproduce the data in the package
        - works with a single package and its direct dependencies
        - reports on reproducability of data packages
        - colored output (red - not reproducible, green - OK)
    - visualize packages and their dependencies as a dependency graph of a repo
