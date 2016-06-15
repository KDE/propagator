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

import os
import sys
import requests

try:
    import simplejson as json
except ImportError:
    import json

class GithubPlugin(object):

    def __init__(self, sfunc):
        cfgPath = os.path.join(os.environ.get("GATOR_CONFIG_PATH"), "RemotesGithub.json")
        with open(cfgPath) as f:
            cfgDict = json.load(f)
            self.mAccessToken = cfgDict.get("accesstoken")
            self.mGithubOrg = cfgDict.get("organization")

        mcfgPath = os.path.join(os.environ.get("GATOR_CONFIG_PATH"), "MasterConfig.json")
        with open(mcfgPath) as f:
            self.mRepoBase = json.load(f).get("RepoRoot")

        self.mSession = requests.Session()
        self.mSession.headers.update({"Accept": "application/vnd.github.v3+json"})
        self.mSession.headers.update({"Authorization": " ".join(("token", self.mAccessToken))})

        self.mSyncFunc = sfunc
        self.mReposEndpoint = "https://api.github.com/repos"
        self.mOrgsEndpoint = "https://api.github.com/orgs"
        self.mTaskMap = {
            "create": self.createRepo,
            "move": self.moveRepo,
            "update": self.syncRepo,
            "delete": self.deleteRepo,
            "setdesc": self.setRepoDescription
        }

    def __repr__(self):
        return "<GitHub Organization Plugin: {}>".format(self.mGithubOrg)

    def keys(self):
        return self.mTaskMap.keys()

    def get(self, key):
        return self.mTaskMap.get(key)

    def stripRepoName(self, name):
        if name.endswith(".git"):
            return name[:-4]
        return name

    def repoExists(self, name):
        url = "{0}/{1}/{2}".format(self.mReposEndpoint, self.mGithubOrg, name)
        r = self.mSession.get(url)
        return ((r.ok) and ("id" in r.json.keys()))

    def createRepo(self, args):
        reponame = self.stripRepoName(args.get("repo"))
        payload = {
            "name": reponame,
            "description": args.get("desc", "This repository has no description"),
            "private": False,
            "has_issues": False,
            "has_wiki": False,
            "has_downloads": False,
            "auto_init": False,
        }

        # if the repo already exists and create if exists is false, exit early
        if not args.get("ifexists") and self.repoExists(reponame):
            return True

        # build up the create request and execute it
        url = "{0}/{1}/{2}".format(self.mOrgsEndpoint, self.mGithubOrg, "repos")
        r = self.mSession.post(url, data = json.dumps(payload))
        return ((r.status_code == 201) and ("id" in r.json.keys()))

    def moveRepo(self, args):
        oldname = self.stripRepoName(args.get("repo"))
        newname = self.stripRepoName(args.get("dest"))
        payload = { "name": newname }
        url = "{0}/{1}/{2}".format(self.mReposEndpoint, self.mGithubOrg, oldname)
        r = self.mSession.patch(url, data = json.dumps(payload))
        return ((r.status_code == 201) and ("id" in r.json.keys()))

    def syncRepo(self, args):
        srcdir = os.path.join(self.mRepoBase, args.get("repo"))
        desturl = "git@github.com:{0}/{1}".format(self.mGithubOrg, args.get("repo"))
        self.createRepo(args)
        return self.mSyncFunc(srcdir, desturl)

    def deleteRepo(self, args):
        repo = self.stripRepoName(args.get("repo"))
        url = "{0}/{1}/{2}".format(self.mReposEndpoint, self.mGithubOrg, repo)
        r = self.mSession.delete(url)
        return (r.status_code == 204)

    def setRepoDescription(self, args):
        repo = self.stripRepoName(args.get("repo"))
        payload = { "description": desc }
        url = "{0}/{1}/{2}".format(self.mReposEndpoint, self.mGithubOrg, repo)
        r = self.mSession.patch(url, data = json.dumps(payload))
        return ((r.status_code == 201) and ("id" in r.json.keys()))

def createTaskMap(sfunc):
    return GithubPlugin(sfunc)
