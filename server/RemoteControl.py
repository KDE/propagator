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

import os

from importlib.machinery import SourceFileLoader
from logbook import Logger

try:
    import simplejson as json
except ImportError:
    import json

from ServerConfig import ServerConfig
from SyncJob import doSync

class RemoteLoader(object):

    def __init__(self):
        self.mLogger = Logger("RemoteLoader")
        self.mLogger.info("loading remote management plugins...")

        defaultSearchPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "remotes")
        self.mPluginsSearchPaths = [ defaultSearchPath ]
        self.mPluginsSearchPaths.extend(ServerConfig.get("RemotePluginsDir", []))

        self.mLoadedPlugins = {}
        self.mTaskMap = {}

        for searchPath in self.mPluginsSearchPaths:
            self.mLogger.info("  loading plugins from directory: {0}", searchPath)
            for pluginDir in os.listdir(searchPath):
                pluginPath = os.path.join(searchPath, pluginDir)
                pluginName, pluginEntry = self.loadPlugin(pluginPath)
                if pluginName:
                    if pluginEntry["meta"].get("pushtype") == "restricted":
                        syncFunc = lambda src, dest: doSync(src, dest, True)
                    else:
                        syncFunc = lambda src, dest: doSync(src, dest, False)
                    self.mLoadedPlugins[pluginName] = pluginEntry
                    self.mTaskMap[pluginName] = pluginEntry.get("instance").createTaskMap(syncFunc)
                    self.mLogger.info("    loaded plugin: {0}".format(pluginName))
        self.mLogger.info("done loading remote management plugins")

    def loadPlugin(self, path):
        metaFile = os.path.join(path, "metadata.json")
        if not os.path.isfile(metaFile):
            return (None, None)

        codeFile = os.path.join(path, "EntryPoint.py")
        if not os.path.isfile(codeFile):
            return (None, None)

        plugin = {}
        with open(metaFile) as f:
            plugin["meta"] = json.load(f)
        pluginName = plugin.get("meta").get("name")
        plugin["instance"] = SourceFileLoader("{0}.EntryPoint".format(pluginName), codeFile).load_module()
        return (pluginName, plugin)

    def listLoadedPlugins(self):
        return self.mLoadedPlugins.keys()

    def taskFunction(self, plugin, taskid):
        if not plugin in self.mLoadedPlugins.keys():
            raise NotImplementedError("plugin {0} is not available".format(plugin))
        if not taskid in self.mTaskMap.get(plugin).keys():
            raise NotImplementedError("plugin {0} does not implement task {1}".format(plugin, taskid))
        return self.mTaskMap.get(plugin).get(taskid)

RemotePlugins = RemoteLoader()
