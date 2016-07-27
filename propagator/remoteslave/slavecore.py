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
import signal
import logbook
import importlib

from propagator import VERSION as version
from propagator.core.config import config_general
from propagator.remoteslave import amqp

class SlaveCore(object):
    def __init__(self, slave_name):
        # set up the logger as early as possible
        self.log = logbook.Logger("RemoteSlave-{}".format(str(os.getpid())))
        self.log.info("This is KDE Propagator {} - Remote Slave".format(version))
        self.log.info("    Starting...")

        # create the operations log handler and load in the slave
        self.opslog = self.init_slave_logger(slave_name)
        self.remote = self.init_slave_module(slave_name)

        # set up the amqp channel, and bind it to the consumer callback
        self.channel = amqp.create_channel_consumer(slave_name)
        self.channel.basic_consume(self.process_single_message, amqp.queue_name_for_slave(slave_name))

    def __call__(self):
        # set up sigterm to also raise KeyboardInterrupt
        signal.signal(signal.SIGTERM, signal.getsignal(signal.SIGINT))

        # run the main loop
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
            self.remote = importlib.import_module(plugin_name)
        except ImportError:
            self.log.critical("remote plugin not found: {}".format(slave_name))
            self.log.critical("this slave will now exit.")
            sys.exit(1)
        self.log.info("loaded remote plugin: {}".format(slave_name))

    def process_single_message(self, channel, method, properties, body):
        print("[*] Body: {}".format(body))
        channel.basic_ack(method.delivery_tag)
