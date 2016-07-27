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

import os
import sys
import argparse
import importlib
import logbook

from propagator import VERSION
from propagator.remoteslave import amqp

def cmdline_process():
    parser = argparse.ArgumentParser(description = "Run a Propagator Remote Slave")
    parser.add_argument("remotename", type = str, help = "Start a slave for this remote type")
    args = parser.parse_args()
    return args.remotename

def main():
    # initialise logging
    logbook.StreamHandler(sys.stdout).push_application()
    log = logbook.Logger("RemoteSlave-{}".format(str(os.getpid())))

    # process the command line and figure out which remote plugin we want to run
    remote_name = cmdline_process()
    log.info("This is KDE Propagator {} - Remote Slave".format(VERSION))
    log.info("    Starting...")
    log.info("remote plugin requested: {}".format(remote_name))
    plugin_name = "propagator.remotes.{}".format(remote_name)
    try:
        remote = importlib.import_module(plugin_name)
    except ImportError:
        log.critical("remote plugin not found: {}".format(remote_name))
        log.critical("this slave will now exit.")
        sys.exit(1)
    log.info("loaded remote plugin: {}".format(remote_name))

    print(" [*] Waiting for logs. To exit press CTRL+C")
    #channel = amqp.create_channel_consumer("logs")
    #channel.basic_consume(callback, amqp.queue_name_for_slave("logs"))
    #channel.start_consuming()

def callback(ch, method, properties, body):
    ch.basic_ack(method.delivery_tag)
    print(" [x] %r" % body)
