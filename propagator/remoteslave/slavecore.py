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

import sys
import os
import git
import pika
import signal
import logbook
import importlib

try:
    import simplejson as json
except ImportError:
    import json

from propagator import VERSION as version
from propagator.core.config import config_general
from propagator.remoteslave import amqp

class SlaveCore(object):
    def __init__(self, slave_name):
        # set up the logger as early as possible
        self.log = logbook.Logger("RemoteSlave-{}".format(str(os.getpid())))
        self.log.info("This is KDE Propagator {} - Remote Slave".format(version))
        self.log.info("    Starting...")

        # create the operations log handler and load in the slave, and other things
        self.opslog = self.init_slave_logger(slave_name)
        self.remote = self.init_slave_module(slave_name).Remote(self.opslog)
        self.repobase = config_general.get("repobase")
        self.max_retries = int(config_general.get("max_retries", 5))
        self.retry_step = int(config_general.get("retry_interval_step", 300)) * 1000
        self.slave_name = slave_name

        # set up the amqp channel, and bind it to the consumer callback
        self.channel = amqp.create_channel_consumer(slave_name)
        self.channel.basic_consume(self.process_single_message, amqp.queue_name_for_slave(slave_name))

    def __call__(self):
        # set up sigterm to also raise KeyboardInterrupt
        signal.signal(signal.SIGTERM, signal.getsignal(signal.SIGINT))
        self.log.info("listening for new tasks...")
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.channel.stop_consuming()
        self.log.info("slave is shutting down...")

    def init_slave_logger(self, slave_name):
        # get the logs directory and ensure that it exists
        default_logdir = os.path.expanduser("~/.propagator/logs")
        logdir = config_general.get("logs_dir", default_logdir)
        if not os.path.isdir(logdir):
            os.makedirs(logdir)

        # fire up a logger with its own handler to redirect to the file
        logpath = os.path.join(logdir, "remote.{}.log".format(slave_name))
        logger = logbook.Logger("slave-{}".format(slave_name))
        logger.handlers.append(logbook.FileHandler(logpath))

        # done, return logger
        return logger

    def init_slave_module(self, slave_name):
        self.log.info("remote plugin requested: {}".format(slave_name))
        plugin_name = "propagator.remotes.{}".format(slave_name)
        try:
            remote = importlib.import_module(plugin_name)
        except ImportError:
            self.log.critical("remote plugin not found: {}".format(slave_name))
            self.log.critical("this slave will now exit.")
            sys.exit(1)
        self.log.info("loaded remote plugin: {}".format(slave_name))
        return remote

    def process_single_message(self, channel, method, properties, body):
        if type(body) is bytes:
            body = body.decode("utf-8")
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.log.error("task malformed: {}".format(body))
            channel.basic_ack(method.delivery_tag)
            return

        # check the retry count
        if not data.get("attempt"):
            data["attempt"] = 0;

        # check if message is conditional to only one slave
        remote_for = data.get("remote_for")
        if (remote_for is not None) and (self.slave_name not in remote_for):
            self.log.debug("skipped conditional task not meant for this slave: {}".format(body))
            channel.basic_ack(method.delivery_tag)
            return

        # check for existence and validity of method
        valid_ops = ("create", "rename", "update", "delete", "syncdesc")
        op = data.get("operation")
        if (not op) or (op not in valid_ops):
            self.log.error("task malformed: invalid or no operation: {}".format(body))
            channel.basic_ack(method.delivery_tag)
            return

        # check for source repo in message
        repo = data.get("repository")
        if not repo:
            self.log.error("task malformed: no repository: {}".format(body))
            channel.basic_ack(method.delivery_tag)
            return

        # check if the repo can be handled by this repo
        if not self.remote.can_handle_repo(repo):
            self.log.debug("repository cannot be handled by this repo, skipping: {}".format(body))
            channel.basic_ack(method.delivery_tag)
            return

        # check if the source repo is valid and exists
        repo = self.get_repo(repo)
        if not repo and op != "delete":
            self.log.error("invalid repository: {}".format(body))
            channel.basic_ack(method.delivery_tag)
            return

        ret = getattr(self, "process_op_{}".format(op))(data, repo)
        if ret is False:
            data["attempt"] = data["attempt"] + 1
            if data["attempt"] > self.max_retries:
                self.fail_permanently(data)
            else:
                message = json.dumps(data)
                backoff = str(self.retry_step * data["attempt"])
                self.channel.basic_publish(
                    exchange = "",
                    routing_key = amqp.delay_queue_name_for_slave(self.slave_name),
                    properties = pika.BasicProperties(expiration = backoff),
                    body = message
                )
        channel.basic_ack(method.delivery_tag)

    def process_op_create(self, data, repo):
        name = data.get("repository")
        try:
            self.remote.create(name, repo.description)
        except Exception:
            self.opslog.error("could not create repository: {}".format(name))
            self.opslog.exception()
            return False
        self.opslog.info("created repository: {}".format(name))

    def process_op_rename(self, data, repo):
        name = data.get("repository")
        dest = data.get("destination")
        if not dest:
            self.log.error("task malformed: no destination: {}".format(body))
            return
        try:
            self.remote.rename(name, dest)
        except Exception:
            self.opslog.error("could not create repository: {}".format(name))
            self.opslog.exception()
            return False
        self.opslog.info("renamed repository: {} -> {}".format(name, dest))

    def process_op_update(self, data, repo):
        name = data.get("repository")
        if not repo.branches:
            self.opslog.info("skipping update of empty repository: {    @abc.abstractmethod}".format(name))
            return
        try:
            self.remote.update(repo, name)
        except Exception:
            self.opslog.error("could not update repository: {}".format(name))
            self.opslog.exception()
            return False
        self.opslog.info("updated repository: {}".format(name))

    def process_op_delete(self, data, repo):
        name = data.get("repository")
        try:
            self.remote.delete(name)
        except Exception:
            self.opslog.error("could not delete repository: {}".format(name))
            self.opslog.exception()
            return False
        self.opslog.info("deleted repository: {}".format(name))

    def process_op_syncdesc(self, data, repo):
        name = data.get("repository")
        try:
            self.remote.setdesc(name, repo.description)
        except Exception:
            self.opslog.error("could not sync repository description: {}".format(name))
            self.opslog.exception()
            return False
        self.opslog.info("synced repository description: {}".format(name))

    def get_repo(self, repo):
        path = os.path.join(self.repobase, repo)
        try:
            repo = git.Repo(path)
        except (git.exc.NoSuchPathError, git.exc.InvalidGitRepositoryError):
            return None
        return repo

    def fail_permanently(self, data):
        pass
