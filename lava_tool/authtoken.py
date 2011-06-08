# Copyright (C) 2011 Linaro Limited
#
# Author: Michael Hudson-Doyle <michael.hudson@linaro.org>
#
# This file is part of lava-tool.
#
# lava-tool is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# as published by the Free Software Foundation
#
# lava-tool is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with lava-tool.  If not, see <http://www.gnu.org/licenses/>.

import base64
import urllib
import xmlrpclib

import keyring.core

from lava_tool.interface import LavaCommandError

class AuthBackend(object):

    def add_token(self, username, hostname, token):
        raise NotImplementedError

    def get_token_for_host(self, user, host):
        raise NotImplementedError


class KeyringAuthBackend(AuthBackend):

    def add_token(self, username, hostname, token):
        keyring.core.set_password("lava-tool-%s" % hostname, username, token)

    def get_token_for_host(self, username, hostname):
        return keyring.core.get_password("lava-tool-%s" % hostname, username)


class MemoryAuthBackend(AuthBackend):

    def __init__(self, user_host_token_list):
        self._tokens = {}
        for user, host, token in user_host_token_list:
            self._tokens[(user, host)] = token

    def add_token(self, username, hostname, token):
        self._tokens[(username, hostname)] = token

    def get_token_for_host(self, username, host):
        return self._tokens.get((username, host))


class AuthenticatingTransportMixin:

    def get_host_info(self, host):

        x509 = {}
        if isinstance(host, tuple):
            host, x509 = host

        auth, host = urllib.splituser(host)

        if auth:
            user, token = urllib.splitpasswd(auth)
            if token is None:
                token = self.auth_backend.get_token_for_host(user, host)
                if token is None:
                    raise LavaCommandError(
                        "Username provided but no token found.")
            auth = base64.b64encode(urllib.unquote(user + ':' + token))
            extra_headers = [
                ("Authorization", "Basic " + auth)
                ]
        else:
            extra_headers = None

        return host, extra_headers, x509


class AuthenticatingTransport(
        AuthenticatingTransportMixin, xmlrpclib.Transport):
    def __init__(self, use_datetime=0, auth_backend=None):
        xmlrpclib.Transport.__init__(self, use_datetime)
        self.auth_backend = auth_backend


class AuthenticatingSafeTransport(
        AuthenticatingTransportMixin, xmlrpclib.SafeTransport):
    def __init__(self, use_datetime=0, auth_backend=None):
        xmlrpclib.SafeTransport.__init__(self, use_datetime)
        self.auth_backend = auth_backend


class AuthenticatingServerProxy(xmlrpclib.ServerProxy):

    def __init__(self, uri, transport=None, encoding=None, verbose=0,
                 allow_none=0, use_datetime=0, auth_backend=None):
        if transport is None:
            if urllib.splittype(uri)[0] == "https":
                transport = AuthenticatingSafeTransport(
                    use_datetime=use_datetime, auth_backend=auth_backend)
            else:
                transport = AuthenticatingTransport(
                    use_datetime=use_datetime, auth_backend=auth_backend)
        xmlrpclib.ServerProxy.__init__(
            self, uri, transport, encoding, verbose, allow_none, use_datetime)
