import os

import git

from const import clone, TMP_DIR


class HAVersion:
    def __init__(self, version):
        self._version = version
        split_version = version.split(".")
        try:
            self.major = int(split_version[0])
        except ValueError:
            self.major = 0
        self.minor = 0
        self.patch = 0
        self.beta = None
        if self.major < 2021:
            return
        
        if len(split_version)>=2:
            self.minor = int(split_version[1])
        if len(split_version)>=3:
            patch = split_version[2].split("b")
            self.patch = int(patch[0])
            if len(patch) == 2:
                self.beta = int(patch[1])


    def __eq__(self, other):
        if (
                self.major==other.major
                and self.minor==self.minor
                and self.patch==self.patch
                and self.beta==self.beta
        ):
            return True
        return False


    def __gt__(self, other):
        if self.major > other.major:
            return True
        elif self.major < other.major:
            return False


        if self.minor > other.minor:
            return True
        elif self.minor < other.minor:
            return False


        if self.patch > other.patch:
            return True
        elif self.patch < other.patch:
            return False


        if self.beta is not None and other.beta is None:
            return False
        elif self.beta is None and other.beta is not None:
            return True
        elif self.beta is None and other.beta is None:
            return False
        elif self.beta > other.beta:
            return True
        return False

def prepare_homeassistant(ref=None):
    if not os.path.isdir(TMP_DIR):
        os.system(clone)  # Cloning

    if ref is None:
        repo = git.Repo(TMP_DIR)
        versions = {str(tag): HAVersion(str(tag)) for tag in repo.tags}
        latest_version = HAVersion("0.0.0")
        for key, version in versions.items():
            if version > latest_version:
                latest_version = version
                ref = key

    repo.head.reference = repo.refs[ref]
    repo.head.reset(index=True, working_tree=True)
    return ref
