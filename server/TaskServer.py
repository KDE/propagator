#!/usr/bin/python3
# This file is part of Propagator, a KDE Sysadmin Project
#
#   Copyright 2015-2016 (C) Boudhayan Gupta <bgupta@kde.org>
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

import sys
import os
import argparse
import traceback

from redis import Redis
from logbook import Logger

from RemoteControl import RemotePlugins

try:
    import simplejson as json
except ImportError:
    import json

class RedisConsumer(object):

    def __init__(self, qkey, host = "localhost", port = 6379, db = 0, password = None):
        self.mLogger = Logger("RedisConsumer")
        self.mRedisConn = Redis(host = host, port = port, db = db, password = password)
        self.mTaskQueueKey = "{}-IncomingTasks".format(qkey)
        self.mFailedQueueKey = "{}-FailedTasks".format(qkey)
        self.mDoneQueueKey = "{}-DoneTasks".format(qkey)

    def runSingleTask(self):
        queueKey, taskJson = (i.decode() for i in self.mRedisConn.blpop(self.mTaskQueueKey))
        task = json.loads(taskJson)

        plugin, taskid = task.get("jobclass").split(":")
        try:
            func = RemotePlugins.taskFunction(plugin, taskid)
            ret = func(task.get("arguments"))
        except Exception:
            task["return"] = None
            task["except"] = True
            task["traceback"] = traceback.format_exc()
            self.mLogger.exception()
            self.mRedisConn.rpush(self.mFailedQueueKey, json.dumps(task))
        else:
            task["return"] = ret
            task["except"] = False
            self.mRedisConn.rpush(self.mDoneQueueKey, json.dumps(task))

    def runProcessLoop(self):
        self.mLogger.info("consumer is now listening for tasks")
        while True: self.runSingleTask()

def CmdlineParse():

    parser = argparse.ArgumentParser(prog = "TaskServer.py", description = "Server to process tasks created by the propagator daemon")
    parser.add_argument("-e", "--eid", dest = "eid", action = "store", default = os.getpid(), help = "set an identifier for the server, for logging purposes (default is pid)")

    return parser.parse_args()

if __name__ == "__main__":

    # parse command line arguments
    info = CmdlineParse()

    # set up logging
    from logbook import StreamHandler, Logger
    StreamHandler(sys.stdout).push_application()
    logger = Logger("TaskServer-{}".format(info.eid))

    # start up
    logger.info("starting...")
    from RemoteControl import RemotePlugins
    print(RemotePlugins.listLoadedPlugins())

    consumer = RedisConsumer("redis-experiment")
    consumer.runProcessLoop()
