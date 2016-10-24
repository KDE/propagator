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

import re
import os
import sys
import requests

try:
    import simplejson as json
except ImportError:
    import json

from propagator.core.sync import restricted_sync
from propagator.core.config import config_general
from propagator.remotes.remotebase import RemoteBase

class Remote(RemoteBase):
    ENDPOINT_REPO = "https://api.github.com/repos"
    ENDPOINT_ORGS = "https://api.github.com/orgs"

    @property
    def plugin_name(self):
        return "github"

    def plugin_init(self, *args, **kwargs):
        cfgpath = os.path.expanduser("~/.propagator/remotes_github.json")
        with open(cfgpath) as f:
            cfgdict = json.load(f)

        self.access_token = cfgdict["access_token"]
        self.organization = cfgdict["organization"]
        self.except_checks = tuple(re.compile(i) for i in cfgdict["excepts"])
        self.repo_base = config_general.get("repobase")

        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/vnd.github.v3+json"})
        self.session.headers.update({"Authorization": " ".join(("token", self.access_token))})

    def _strip_reponame(self, name):
        if name.endswith(".git"):
            return name[:-4]
        return name

    def _repo_exists(self, name):
        url = "{0}/{1}/{2}".format(self.ENDPOINT_REPO, self.organization, name)
        r = self.session.get(url)
        return ((r.ok) and ("id" in r.json().keys()))

    def can_handle_repo(self, name):
        name = self._strip_reponame(name)
        for i in self.except_checks:
            if (i.match(name)): return False
        return True

    def create(self, name, desc = "This repository has no description"):
        name = self._strip_reponame(name)

        # if the repo already exists, exit early
        if self._repo_exists(name): return True

        # build up the create request and execute it
        payload = {
            "name": name,
            "description": desc,
            "private": False,
            "has_issues": False,
            "has_wiki": False,
            "has_downloads": False,
            "auto_init": False,
        }
        url = "{0}/{1}/{2}".format(self.ENDPOINT_ORGS, self.organization, "repos")
        r = self.session.post(url, data = json.dumps(payload))
        return ((r.status_code == 201) and ("id" in r.json().keys()))

    def rename(self, name, dest):
        name = self._strip_reponame(name)
        dest = self._strip_reponame(dest)
        payload = { "name": dest }
        url = "{0}/{1}/{2}".format(self.ENDPOINT_REPO, self.organization, name)
        r = self.session.patch(url, data = json.dumps(payload))
        return ((r.status_code == 201) and ("id" in r.json().keys()))

    def update(self, repo, name):
        srcdir = os.path.join(self.repo_base, name)
        desturl = "git@github.com:{0}/{1}".format(self.organization, name)
        if not self._repo_exists(name):
            self.create(name, repo.description)
        return restricted_sync(srcdir, desturl)

    def delete(self, name):
        name = self._strip_reponame(name)
        url = "{0}/{1}/{2}".format(self.ENDPOINT_REPO, self.organization, name)
        r = self.session.delete(url)
        return (r.status_code == 204)

    def setdesc(self, name, desc):
        name = self._strip_reponame(name)
        payload = { "name": name, "description": desc }
        url = "{0}/{1}/{2}".format(self.ENDPOINT_REPO, self.organization, name)
        r = self.session.patch(url, data = json.dumps(payload))
        return ((r.status_code == 201) and ("id" in r.json().keys()))
