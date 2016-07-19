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

import os
import shlex
import shutil

from . import repo
from . import config

def help():
    print("Propagator - A git mirror fleet manager")
    print("anongitctl help")
    print("")
    print("Subcommands:")
    print("  create <reponame> [description]  - create repository with description")
    print("  rename <oldrepo> <newrepo>       - move/rename and existing repository")
    print("  delete <reponame>                - delete a repository")
    print("  setdesc <reponame> <description> - set the description of an existing repository")
    print("")

def setdesc(path, desc):
    if not repo.set_repo_description(path, desc):
        return False
    print("OK: Description successfully set.")
    return True

def create(path, desc = None):
    if not repo.create(path, False):
        return False
    print("OK: Repository successfully created.")
    if desc:
        return setdesc(path, desc)
    return True

def rename(oldpath, newpath):
    if not os.path.exists(oldpath):
        print("ERROR: Source repo does not exist.")
        return False
    if os.path.exists(newpath):
        print("ERROR: Destination repo already exists.")
        return False
    basepath = os.path.dirname(newpath)
    if not os.path.exists(basepath):
        os.makedirs(basepath)
    shutil.move(oldpath, newpath)
    print("OK: Repository successfully renamed.")
    return True

def delete(path):
    if not os.path.exists(path):
        print("ERROR: Repository does not exist.")
        return False
    shutil.rmtree(path)
    print("OK: Repository successfully deleted.")
    return True

def handle_command(cmd):
    cmd_parts = shlex.split(cmd)
    if not cmd_parts[1] in ("create", "rename", "delete", "setdesc", "help"):
        print("ERROR: Invalid anongitctl subcommand.")
        help()
        return False
    if cmd_parts[1] == "help":
        help()
        return True

    try:
        reponame = config.translate_path(cmd_parts[2])
    except IndexError:
        print("ERROR: Incorrect command syntax.")
        help()
        return False

    if cmd_parts[1] == "create":
        try:
            desc = cmd_parts[3]
        except IndexError:
            desc = None
        return create(reponame, desc)
    elif cmd_parts[1] == "rename":
        try:
            newname = config.translate_path(cmd_parts[3])
        except IndexError:
            print("ERROR: Incorrect command syntax.")
            help()
            return False
        return rename(reponame, newname)
    elif cmd_parts[1] == "delete":
        return delete(reponame)
    elif cmd_parts[1] == "setdesc":
        try:
            desc = cmd_parts[3]
        except IndexError:
            print("ERROR: Incorrect command syntax.")
            help()
            return False
        return setdesc(reponame, desc)
    print("ERROR: Unknown error.")
    return False
