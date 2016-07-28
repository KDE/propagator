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

import pika
from propagator.core.config import config_amqp

queue_name_for_slave = lambda slave_name: "propagator.slave.{}".format(slave_name)
delay_queue_name_for_slave = lambda slave_name: "propagator.slave.{}.delay".format(slave_name)
exchange_name = lambda: "propagator.exchange.master"
delay_exchange_name = lambda: "propagator.exchange.delay"

def create_channel():
    # get the relevant configuration and set sane defaults
    amqp_user = config_amqp.get("user", "guest")
    amqp_pass = config_amqp.get("pass", "guest")
    amqp_host = config_amqp.get("host", "localhost")
    amqp_port = config_amqp.get("port", 5672)
    amqp_vhost = config_amqp.get("vhost", "/")

    # connect to the amqp server
    creds = pika.PlainCredentials(amqp_user, amqp_pass)
    params = pika.ConnectionParameters(amqp_host, amqp_port, amqp_vhost, creds)
    conn = pika.BlockingConnection(params)
    channel = conn.channel()

    # done, return channel
    return channel

def prepare_channel_producer(channel):
    # just declare the exchange and return the channel
    channel.exchange_declare(exchange = exchange_name(), exchange_type = "fanout", auto_delete = True)
    return channel

def prepare_channel_consumer(channel, slave_name):
    # we need the exchange declared too...
    channel = prepare_channel_producer(channel)

    # declare the message exchange and a queue for the slave, and bind them
    queue_name = queue_name_for_slave(slave_name)
    channel.queue_declare(queue = queue_name, auto_delete = True)
    channel.queue_bind(queue = queue_name, exchange = exchange_name())

    # ...and the dead-letter exchange
    delay_queue_name = delay_queue_name_for_slave(slave_name)
    channel.exchange_declare(exchange = delay_exchange_name(), exchange_type = "direct", auto_delete = True)
    channel.queue_declare(queue = delay_queue_name, durable = True, arguments = {
        "x-dead-letter-exchange": delay_exchange_name(),
        "x-dead-letter-routing-key": queue_name
    })
    channel.queue_bind(queue = queue_name, exchange = delay_exchange_name(), routing_key = queue_name)

    # done, return channel
    return channel

def create_channel_producer():
    channel = create_channel()
    return prepare_channel_producer(channel)

def create_channel_consumer(slave_name):
    channel = create_channel()
    return prepare_channel_consumer(channel, slave_name)
