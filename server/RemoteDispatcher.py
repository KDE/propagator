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
