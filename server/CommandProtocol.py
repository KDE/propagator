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

from datetime import datetime
from collections import namedtuple
from ServerConfig import ServerConfig

# task dispatcher
from RemoteControl import RemotePlugins
from RemoteDispatcher import RemoteDispatcher
dispatcher = RemoteDispatcher(RemotePlugins, "redis-experiment")

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

# protocol parse helpers

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
        dispatcher.createRepo(context.arguments.get("srcRepo"), ident = context.upstream)
    elif context.action == "update":
        dispatcher.updateRepo(context.arguments.get("srcRepo"), ident = context.upstream)
    elif context.action == "delete":
        dispatcher.deleteRepo(context.arguments.get("srcRepo"), ident = context.upstream)
    elif context.action == "rename":
        dispatcher.moveRepo(context.arguments.get("srcRepo"), context.arguments.get("destRepo"), ident = context.upstream)
