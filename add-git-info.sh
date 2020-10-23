#!/bin/bash
# GIT_REPO   = "git@github.com:e3krisztian/bead.git"
# GIT_BRANCH = "master"
# GIT_DATE   = "2020-10-11T01:14:36+02:00"
# GIT_HASH   = "ff43a47"
# DIRTY      = True | False

if git status --short |
       # drop untracked
       grep -v '^[?][?]' |
       # ignore changes in version file
       fgrep -v ' bead_cli/git_info.py' |
       # do we have any remaining?
       grep . > /dev/null
then
    DIRTY=True
else
    DIRTY=False
fi

cat > bead_cli/git_info.py <<EOF
# generated - do not edit
GIT_REPO    = "$(git config --get remote.origin.url)"
GIT_BRANCH  = "$(git branch --show-current)"
GIT_DATE    = "$(git show HEAD --pretty=tformat:'%cI' --no-patch)"
GIT_HASH    = "$(git show HEAD --pretty=tformat:'%h' --no-patch)"
TAG_VERSION = "$(git describe --tags)"
DIRTY       = $DIRTY
EOF
