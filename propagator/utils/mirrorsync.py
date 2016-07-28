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
import argparse

try:
    import simplejson as json
except ImportError:
    import json

from propagator.utils.common import is_valid_repo
from propagator.remoteslave import amqp

def cmdline_process():
    parser = argparse.ArgumentParser(description = "Sync updates to all repository mirrors through Propagator")
    parser.add_argument("reponame", type = str, help = "the name of the repository to update")
    parser.add_argument("remote", type = str, nargs = "*", help = "update only these remotes")
    parser.add_argument("-v", "--verbose", action = "store_true", help = "give verbose output on the standard output")
    args = parser.parse_args()
    return args

def send_message(payload):
    body = json.dumps(payload)
    channel = amqp.create_channel_producer()
    return channel.basic_publish(
        exchange = amqp.exchange_name(),
        routing_key = "",
        body = body
    )

def main():
    args = cmdline_process()
    if not (is_valid_repo(args.reponame)):
        print("ERROR: {} is not a valid repository".format(args.reponame), file = sys.stderr)
        sys.exit(1)
    message = { "operation": "update", "repository": args.reponame, "attempt": 0 }
    if args.remote:
        message["remote_for"] = parser.remote
    ret = send_message(message)
    if not ret:
        print("ERROR: Failed to notify Propagator to update repository mirrors")
        sys.exit(1)
    if args.verbose:
        print("Successfully notified Propagator to update repository mirrors")
    sys.exit(0)
