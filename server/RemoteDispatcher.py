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

from logbook import Logger
from redis import Redis
from uuid import uuid4

try:
    import simplejson as json
except ImportError:
    import json

class RemoteDispatcher(object):

    def __init__(self, loader, qkey, host = "localhost", port = 6379, db = 0, password = None):
        self.mLogger = Logger("RemoteDispatcher")
        self.mLogger.info("connecting to the redis task queue...")
        self.mRedisConn = Redis(host = host, port = port, db = db, password = password)
        self.mQueueKey = "{}-IncomingTasks".format(qkey)
        self.mLogger.info("connected")
        self.mRemoteLoader = loader

    def createJob(self, plugin, jobclass, argsdict, depends = None):
        jobid = "{0}-{1}".format(plugin, str(uuid4()))
        payload = {
            "jobclass": "{0}:{1}".format(plugin, jobclass),
            "jobid": jobid,
            "arguments": argsdict,
            "depends": depends
        }
        self.mRedisConn.rpush(self.mQueueKey, json.dumps(payload))
        return jobid

    def createRepo(self, repo, desc = None, ifexists = False, ident = None):
        for plugin in self.mRemoteLoader.listLoadedPlugins():
            createArgs = { "repo": repo, "desc": desc, "ifexists": ifexists }
            self.createJob(plugin, "createrepo", createArgs)

    def setRepoDescription(self, repo, desc = None, ident = None):
        for plugin in self.mRemoteLoader.listLoadedPlugins():
            descArgs = { "repo": repo, "desc": desc }
            self.createJob(plugin, "setdesc", descArgs)

    def moveRepo(self, repo, dest, ident = None):
        for plugin in self.mRemoteLoader.listLoadedPlugins():
            moveArgs = { "repo": repo, "dest": dest }
            self.createJob(plugin, "moverepo", moveArgs)

    def updateRepo(self, repo, ident = None):
        for plugin in self.mRemoteLoader.listLoadedPlugins():
            upArgs = { "repo": repo }
            self.createjob(plugin, "updaterepo", upArgs)

    def deleteRepo(self, repo, ident = None):
        for plugin in self.mRemoteLoader.listLoadedPlugins():
            delArgs = { "repo": repo }
            self.createJob(plugin, "deleterepo", createArgs)
