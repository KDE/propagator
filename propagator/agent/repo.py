# This file is part of Propagator, a KDE project
#
# Copyright 2015 Boudhayan Gupta <bgupta@kde.org>
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of KDE e.V. (or its successor approved by the
#    membership of KDE e.V.) nor the names of its contributors may be used
#    to endorse or promote products derived from this software without
#    specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR "AS IS" AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import git
import os

def create(path, exists = True):
    try:
        repo = git.Repo(path)
    except git.exc.NoSuchPathError:
        git.Repo.init(path, bare = True)
        return True
    except git.exc.InvalidGitRepositoryError:
        if not os.listdir(path):
            git.Repo.init(path, bare = True)
            return True
        print("ERROR: The remote path is not a valid git repository.")
        return False
    if not repo.bare:
        print("ERROR: The remote repository is not bare. Cannot push.")
        return False
    if not exists:
        print("ERROR: The remote repository already exists.")
    return exists

def set_repo_description(path, desc):
    descfile = os.path.join(path, "description")
    if not os.path.isfile(descfile):
        print("ERROR: Invalid or non-existent repository. Cannot find description file.")
        return False
    with open(descfile, "w") as f:
        print(desc.strip(), file = f)
    return True
