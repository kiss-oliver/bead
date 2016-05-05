# Some use cases

- [create a new data package from existing database](#create-from-data)
- [derive a new data package from existing data packages by computation](#derive-new)
- [update a data package for new input data (create a new version)](#update-with-new-data)
- [update algorithm to create a data package (create a new version)](#update-with-new-algorithm)
- [use data in data package without the tool](#oblivous-use)
- visualize data flow
- create a reproducible set of data packages
- publish how-to-reproduce document


# Use case details

## <a name="create-from-data"></a>Create a new data package from existing  database

There are existing data that are to be converted to packages.

- `bead new PACKAGE-NAME`  (create workspace for a new package)
- `cp data-files PACKAGE-NAME/output`  (copy data into workspace)
- `cd PACKAGE-NAME`
- `bead pack --to REPOSITORY`  (create package from workspace)


## <a name="derive-new"></a>Derive a new data package from existing data packages by computation

- `bead new PACKAGE-NAME`  (create workspace for a new package)
- `cd PACKAGE-NAME`
- `bead mount PACKAGE1 NAME1`  (make data from `PACKAGE1` [version] available at `input/NAME1`)
- ...
- `bead mount PACKAGEn NAMEn`  (make data from `PACKAGEn` [version] available at `input/NAMEn`)
- create some program under the current directory (e.g. python or STATA scripts) that uses data from `input` and produces some data under `output`
- run the program
- `bead pack --to REPOSITORY`  (create package from workspace)


## <a name="update-with-new-data"></a>Update a data package for new input data (create a new version)

- `bead develop PACKAGE-NAME`  (create workspace )
- `cd PACKAGE-NAME`
- `bead update NEW-INPUT-NAME` (update data at `input/NEW-INPUT-NAME` from the newest version of the mounted package)
- run the program
- `bead pack`


## <a name="update-with-new-algorithm"></a>Update algorithm to create a data package (create a new version)

- `bead develop PACKAGE-NAME`  (create workspace )
- `cd PACKAGE-NAME`
- modify code
- run the program
- `bead pack`

## <a name="oblivous-use"></a>Use data in data package without the tool

Package is a zip file, so with an unarchiver the data can be extracted.
