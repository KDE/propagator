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
import collections

try:
    import simplejson as json
except ImportError:
    import json

class SyncedJSONDict(collections.UserDict):

    def __init__(self, filename, autoSync = False):
        self.jsonFilename = filename
        self.isDirty = False
        self.autoSync = autoSync

        if os.path.isfile(self.jsonFilename):
            self.syncRead()

    def syncWrite(self):
        if self.isDirty:
            with open(self.jsonFilename, "w") as f:
                f.write(json.dumps(self.data, indent = 4, sort_keys = True))
            self.isDirty = False

    def syncRead(self):
        with open(self.jsonFilename, "r") as f:
            self.data = json.load(f)
        self.isDirty = False

    def __setitem__(self, key, item):
        super().__setitem__(key, item)
        self.isDirty = True
        if self.autoSync:
            self.syncWrite()

    def __delitem__(self, key):
        super().__delitem__(key, item)
        self.isDirty = True
        if self.autoSync:
            self.syncWrite()

    def clear(self):
        super().clear()
        self.isDirty = True
        if self.autoSync:
            self.syncWrite()

    def pop(self, key, *args):
        ret = super().pop(key, *args)
        self.isDirty = True
        if self.autoSync:
            self.syncWrite()
        return ret

    def popitem(self):
        ret = super().popitem()
        self.isDirty = True
        if self.autoSync:
            self.syncWrite()
        return ret

    def update(self, dict = None):
        if dict is None:
            pass
        elif isinstance(dict, UserDict.UserDict):
            self.data = dict.data
            self.isDirty = True
            if self.autoSync:
                self.syncWrite()
        elif isinstance(dict, type({})):
            self.data = dict
            self.isDirty = True
            if self.autoSync:
                self.syncWrite()
        else:
            raise TypeError

# load the main propagator configuration
ConfigPath = os.path.join(os.environ.get("GATOR_CONFIG_PATH"), "MasterConfig.json")
ServerConfig = SyncedJSONDict(ConfigPath)
