# This file is part of Propagator, a KDE Sysadmin Project
#
# Copyright 2016 Boudhayan Gupta <bgupta@kde.org>
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

from propagator.utils.common import is_valid_repo, send_message, allowed_ops, set_local_desc

def cmdline_process():
    parser = argparse.ArgumentParser(description = "Propagator Mirror Control Utility")
    parser.add_argument("action", type = str, help = "the action to perform on the repo", choices = allowed_ops)
    parser.add_argument("reponame", type = str, help = "the name of the repository to update")
    parser.add_argument("-D", "--dest", type = str, help = "the new name for the renamed repository", required = False)
    parser.add_argument("-d", "--desc", type = str, help = "the new description for the repository", required = False)
    parser.add_argument("remote", type = str, nargs = "*", help = "update only these remotes")

    args = parser.parse_args()
    if (args.action ==  "rename") and (not args.dest):
        parser.error("The rename action requires a specified restination")
    return args

def main():
    args = cmdline_process()
    if (args.action == "update") and (not is_valid_repo(args.reponame)):
        print("ERROR: {} is not a valid repository".format(args.reponame), file = sys.stderr)
        sys.exit(1)

    # compose the message
    message = {
        "operation": args.action,
        "repository": args.reponame,
        "attempt": 0
    }

    # compose optional extras in the message
    if (args.action == "rename"):
        message["destination"] = args.dest
    if (args.action == "syncdesc") and args.desc:
        if not set_local_desc(args.reponame, args.desc):
            print("ERROR: Unable to set description on the local repository")
            sys.exit(1)
    if args.remote:
        message["remote_for"] = args.remote

    # send the message and analyse the fallout
    ret = send_message(message)
    if not ret:
        print("ERROR: Failed to notify Propagator. Please check if the AMQP server is running")
        sys.exit(1)
    print("SUCCESS: Propagator has been notified")
    sys.exit(0)
