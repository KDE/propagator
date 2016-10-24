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

import git
import os

try:
    import simplejson as json
except ImportError:
    import json

from propagator.core.config import config_general
from propagator.remoteslave import amqp

# Data First

allowed_ops = ("create", "update", "rename", "delete", "syncdesc")

# Methods

def send_message(payload):
    body = json.dumps(payload)
    channel = amqp.create_channel_producer()
    return channel.basic_publish(
        exchange = amqp.exchange_name(),
        routing_key = "",
        body = body
    )

def is_valid_repo(repo):
    path = os.path.join(config_general.get("repobase"), repo)
    try:
        repo = git.Repo(path)
    except (git.exc.NoSuchPathError, git.exc.InvalidGitRepositoryError):
        return False
    return True

def set_local_desc(repo, desc):
    path = os.path.join(config_general.get("repobase"), repo)
    repo = git.Repo(path)
    try:
        repo.description = desc
    except Exception:
        return False
    return True
