# This file is part of Propagator, a KDE Sysadmin Project
#
#   Copyright (C) 2015-2016 Boudhayan Gupta <bgupta@kde.org>
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

import os
import shlex
import celery

from datetime import datetime
from collections import namedtuple

import CeleryWorkers
from ServerConfig import ServerConfig

# protocol exceptions

class PropagatorProtocolException(Exception):

    def logline(self):
        time = datetime.now().strftime("%Y-%m-%d %k:%M:%S")
        return "{0} | {1}\n".format(time, str(self))

class InvalidCommandException(PropagatorProtocolException):

    def __init__(self, desc, command):
        self.description = desc
        self.command = command
        super(InvalidCommandException, self).__init__("{0}: {1}".format(desc, command))

class InvalidActionException(PropagatorProtocolException):

    def __init__(self, action):
        self.action = action
        super(InvalidActionException, self).__init__("Invalid command: {0}".format(action))

# helper functions

def isExcluded(repo, config):

    for pattern in config:
        p = re.compile(pattern)
        if p.match(repo):
            return True
    return False

def CreateRepo(repo, upSpec):

    # find our repository and read in the description
    repoRoot = ServerConfig.get("RepoRoot")
    repoPath = os.path.join(repoRoot, repo)
    if not os.path.exists(repoPath):
        return

    repoDesc = "This repository has no description"
    repoDescFile = os.path.join(repoPath, "description")
    if os.path.exists(repoDescFile):
        with open(repoDescFile) as f:
            repoDesc = f.read().strip()

    # spawn the create tasks
    if ServerConfig.get("GithubEnabled") and (not isExcluded(repo, ServerConfig.get("GithubExcepts"))):
        CeleryWorkers.CreateRepoGithub.delay(repo, repoDesc)

    if ServerConfig.get("AnongitEnabled") and (not isExcluded(repo, ServerConfig.get("AnongitExcepts"))):
        for server in ServerConfig.get("AnongitServers"):
            CeleryWorkers.CreateRepoAnongit.delay(repo, server, repoDesc)

def RenameRepo(srcRepo, destRepo, upSpec):

    if ServerConfig.get("GithubEnabled") and (not isExcluded(repo, ServerConfig.get("GithubExcepts"))):
        CeleryWorkers.MoveRepoGithub.delay(srcRepo, destRepo)

    if ServerConfig.get("AnongitEnabled") and (not isExcluded(repo, ServerConfig.get("AnongitExcepts"))):
        for server in ServerConfig.get("AnongitServers"):
            CeleryWorkers.CreateRepoAnongit.delay(srcRepo, destRepo, server)

def UpdateRepo(repo, upSpec):

    # find our repository
    repoRoot = ServerConfig.get("RepoRoot")
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
    if ServerConfig.get("GithubEnabled") and (not isExcluded(repo, ServerConfig.get("GithubExcepts"))):
        githubPrefix = ServerConfig.get("GithubPrefix")
        githubUser = ServerConfig.get("GithubUser")
        githubRemote = "%s@github.com:%s/%s" % (githubUser, githubPrefix, repo)

        createTask = CeleryWorkers.CreateRepoGithub.si(repo, repoDesc)
        syncTask = CeleryWorkers.SyncRepo.si(repoPath, githubRemote, True)
        celery.chain(createTask, syncTask)()

    # now spawn all push to anongit tasks
    if ServerConfig.get("AnongitEnabled") and (not isExcluded(repo, ServerConfig.get("AnongitExcepts"))):
        anonUser = ServerConfig.get("AnongitUser")
        anonPrefix = ServerConfig.get("AnongitPrefix")
        for server in ServerConfig.get("AnongitServers"):
            anonRemote = "%s@%s:%s/%s" % (anonUser, server, anonPrefix, repo)

            createTask = CeleryWorkers.CreateRepoAnongit.si(repo, server, repoDesc)
            syncTask = CeleryWorkers.SyncRepo.si(repoPath, anonRemote, False)
            celery.chain(createTask, syncTask)()

def DeleteRepo(repo, upSpec):

    if ServerConfig.get("GithubEnabled") and (not isExcluded(repo, ServerConfig.get("GithubExcepts"))):
        CeleryWorkers.DeleteRepoGithub.delay(repo)

    if ServerConfig.get("AnongitEnabled") and (not isExcluded(repo, ServerConfig.get("AnongitExcepts"))):
        for server in ServerConfig.get("AnongitServers"):
            CeleryWorkers.DeleteRepoAnongit.delay(repo, server)

def ParseCommand(cmdString):

    components = shlex.split(cmdString)
    action = components[0].lower()

    if not action in ("create", "rename", "delete", "update"):
        raise InvalidActionException(action)
    ActionCommand = namedtuple("ActionCommand", ["action", "arguments", "upstream"])

    if action == "create":
        try:
            args = { "srcRepo": components[1] }
        except IndexError:
            raise InvalidCommandException("create command does not contain source repository details", cmdString)
        try:
            upstream = components[2]
        except IndexError:
            upstream = None
    elif action == "update":
        try:
            args = { "srcRepo": components[1] }
        except IndexError:
            raise InvalidCommandException("update command does not contain source repository details", cmdString)
        try:
            upstream = components[2]
        except IndexError:
            upstream = None
    elif action == "delete":
        try:
            args = { "srcRepo": components[1] }
        except IndexError:
            raise InvalidCommandException("delete command does not contain source repository details", cmdString)
        try:
            upstream = components[2]
        except IndexError:
            upstream = None
    elif action == "rename":
        try:
            args = { "srcRepo": components[1], "destRepo": components[2] }
        except IndexError:
            raise InvalidCommandException("rename command does not contain source and/or destination repository details", cmdString)
        try:
            upstream = components[3]
        except IndexError:
            upstream = None
    return ActionCommand(action, args, upstream)

def ExecuteCommand(context):

    if context.action == "create":
        CreateRepo(context.arguments.get("srcRepo"), context.upstream)
    elif context.action == "update":
        UpdateRepo(context.arguments.get("srcRepo"), context.upstream)
    elif context.action == "delete":
        DeleteRepo(context.arguments.get("srcRepo"), context.upstream)
    elif context.action == "rename":
        RenameRepo(context.arguments.get("srcRepo"), context.arguments.get("destRepo"), context.upstream)
