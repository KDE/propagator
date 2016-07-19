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

import shlex
import os
import sys

from . import config
from . import repo

def analyse_command(cmd):
    cmd_parts_old = shlex.split(cmd)
    cmd_parts_new = []
    repopath = None

    for item in cmd_parts_old:
        if item.endswith(".git"):
            repopath = config.translate_path(item)
            cmd_parts_new.append("'{}'".format(repopath))
        else:
            cmd_parts_new.append(item)
    if not repopath:
        return False

    cmdstring = " ".join(cmd_parts_new)
    return (repopath, cmdstring)

def handle_command(cmd):
    try:
        repopath, cmdstring = analyse_command(cmd)
    except TypeError:
        return False
    repopath = config.translate_path(repopath)

    if cmdstring.startswith("git-receive-pack"):
        ret = repo.create(repopath)
        if not ret:
            print("ERROR: The remote repository does not exist and could not be created", file = sys.stderr)
            return False

    args = ["git-shell", "-c", cmdstring]
    os.execvp("git-shell", args)
