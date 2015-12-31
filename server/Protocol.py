# This file is part of Propagator, a KDE Sysadmin Project
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

# Protocol Description:
#
# CREATE reponame - create reponame.git on server and mirrors
# RENAME oldrepo newrepo - move/rename oldrepo.git to newrepo.git
# UPDATE reponame - sync reponame.git with its mirrors
# DELETE reponame - delete reponame.git
# FLUSH - try to commit all pending updates

import asyncio
import os
import celery

try:
    import simplejson as json
except ImportError:
    import json

import CeleryWorkers

# import our configuration

CFGFILE = os.environ.get("GATOR_CONFIG_FILE")
CFGDATA = {}
with open(CFGFILE) as f:
    CFGDATA = json.load(f)

# helper functions

def isExcluded(repo, config):

    for pattern in config:
        p = re.compile(pattern)
        if p.match(repo):
            return True
    return False

def CreateRepo(repo):

    # find our repository and read in the description
    repoRoot = CFGDATA.get("RepoRoot")
    repoPath = os.path.join(repoRoot, repo)
    if not os.path.exists(repoPath):
        return

    repoDesc = "This repository has no description"
    repoDescFile = os.path.join(repoPath, "description")
    if os.path.exists(repoDescFile):
        with open(repoDescFile) as f:
            repoDesc = f.read().strip()

    # spawn the create tasks
    if CFGDATA.get("GithubEnabled") and (not isExcluded(repo, CFGDATA.get("GithubExcepts"))):
        CeleryWorkers.CreateRepoGithub.delay(repo, repoDesc)

    if CFGDATA.get("AnongitEnabled") and (not isExcluded(repo, CFGDATA.get("AnongitExcepts"))):
        for server in CFGDATA.get("AnongitServers"):
            CeleryWorkers.CreateRepoAnongit.delay(repo, server, repoDesc)

def RenameRepo(srcRepo, destRepo):

    if CFGDATA.get("GithubEnabled") and (not isExcluded(repo, CFGDATA.get("GithubExcepts"))):
        CeleryWorkers.MoveRepoGithub.delay(srcRepo, destRepo)

    if CFGDATA.get("AnongitEnabled") and (not isExcluded(repo, CFGDATA.get("AnongitExcepts"))):
        for server in CFGDATA.get("AnongitServers"):
            CeleryWorkers.CreateRepoAnongit.delay(srcRepo, destRepo, server)

def UpdateRepo(repo):

    # find our repository
    repoRoot = CFGDATA.get("RepoRoot")
    repoPath = os.path.join(repoRoot, repo)
    if not os.path.exists(repoPath):
        return

    # lift the repo description as we might need to create the repo first
    repoDesc = "This repository has no description"
    repoDescFile = os.path.join(repoPath, "description")
    if os.path.exists(repoDescFile):
        with open(repoDescFile) as f:
            repoDesc = f.read().strip()

    # spawn push to github task first
    if CFGDATA.get("GithubEnabled") and (not isExcluded(repo, CFGDATA.get("GithubExcepts"))):
        githubPrefix = CFGDATA.get("GithubPrefix")
        githubUser = CFGDATA.get("GithubUser")
        githubRemote = "%s@github.com:%s/%s" % (githubUser, githubPrefix, repo)

        createTask = CeleryWorkers.CreateRepoGithub.si(repo, repoDesc)
        syncTask = CeleryWorkers.SyncRepo.si(repoPath, githubRemote, True)
        celery.chain(createTask, syncTask)()

    # now spawn all push to anongit tasks
    if CFGDATA.get("AnongitEnabled") and (not isExcluded(repo, CFGDATA.get("AnongitExcepts"))):
        anonUser = CFGDATA.get("AnongitUser")
        anonPrefix = CFGDATA.get("AnongitPrefix")
        for server in CFGDATA.get("AnongitServers"):
            anonRemote = "%s@%s:%s/%s" % (anonUser, server, anonPrefix, repo)

            createTask = CeleryWorkers.CreateRepoAnongit.si(repo, server, repoDesc)
            syncTask = CeleryWorkers.SyncRepo.si(repoPath, anonRemote, False)
            celery.chain(createTask, syncTask)()

def DeleteRepo(repo):

    if CFGDATA.get("GithubEnabled") and (not isExcluded(repo, CFGDATA.get("GithubExcepts"))):
        CeleryWorkers.DeleteRepoGithub.delay(repo)

    if CFGDATA.get("AnongitEnabled") and (not isExcluded(repo, CFGDATA.get("AnongitExcepts"))):
        for server in CFGDATA.get("AnongitServers"):
            CeleryWorkers.DeleteRepoAnongit.delay(repo, server)

class CommandProtocol(asyncio.Protocol):

    def connection_made(self, transport):
        self.transport = transport

    def connection_lost(self, exc):
        self.transport.close()

    def data_received(self, data):
        message = data.decode().strip()
        components = message.split(" ")

        command = components[0]
        if command not in ("CREATE", "RENAME", "UPDATE", "DELETE", "FLUSH"):
            # log invalid command somewhere
            return
        sourceRepo = components[1]

        if command == "CREATE":
            CreateRepo(sourceRepo)
        elif command == "RENAME":
            destRepo = components[2]
            RenameRepo(sourceRepo, destRepo)
        elif command == "UPDATE":
            UpdateRepo(sourceRepo)
        elif command == "DELETE":
            DeleteRepo(sourceRepo)
