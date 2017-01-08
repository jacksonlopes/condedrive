# -*- coding: utf-8 -*-
"""Authenticate and sync.

__author__ = Jackson Lopes
__email__  = jacksonlopes@gmail.com
"""
import os
import logging
from threading import Thread
import onedrivesdk
from condeutils import CondeUtils
from condeconstants import CondeConstants
from condesynclocal import CondeSyncLocal
from condesyncremote import CondeSyncRemote
from condetoken import CondeToken

class CondeDrive(object):
    """Class for authenticate and init sync."""
    redirect_uri  = None
    client_secret = None
    client_id     = None
    scopes        = None
    client        = None
    log           = None
    cutils        = None
    default_remote_dir = CondeConstants().DEFAULT_ONEDRIVE_DIR
    log = logging.getLogger(CondeConstants().LOGGER_NAME)

    def __init__(self, redirect_uri, client_secret, client_id, scopes):
        self.redirect_uri = redirect_uri
        self.client_secret = client_secret
        self.client_id = client_id
        self.scopes = scopes
        self.cutils = CondeUtils()

    def authenticate(self):
        """Authenticate in onedrive.
           
           Args:
             None
           Returns:
             None
        """
        self.log.info("* Authenticating...")

        api_base_url = CondeConstants().API_BASE_URL
        http_provider = onedrivesdk.HttpProvider()
        auth_provider = onedrivesdk.AuthProvider(
            http_provider=http_provider,
            client_id=self.client_id,
            scopes=self.scopes)

        if self.cutils.check_exists_path("session.pickle"):
            self.client = onedrivesdk.OneDriveClient(api_base_url, auth_provider, http_provider)
            self.client.auth_provider.load_session()
            self.client.auth_provider.refresh_token()
        else:
            self.client = onedrivesdk.OneDriveClient(api_base_url, auth_provider, http_provider)
            auth_url = self.client.auth_provider.get_auth_url(self.redirect_uri)
            print("Paste this URL into your browser, approve the app\'s access.")
            print("Copy everything in the address bar after 'code=', and paste it below.")
            print(auth_url)
            code = input('Paste code here: ')
            self.client.auth_provider.authenticate(code, self.redirect_uri, self.client_secret)
            self.client.auth_provider.save_session()

    def sync(self, dir_sync, dir_rules):
        """Sync local <==> onedrive.

           Args:
             dir_sync (array): list directory in format: {'/home/jsl/imagens/teste_conde': 'Pictures/teste_conde'}]
             dir_rules (dict):  rules upload/download only
           Returns:
             None
        """
        try:
            slocal = CondeSyncLocal(self.client, dir_sync, dir_rules)
            sremote = CondeSyncRemote(self.client, dir_sync, dir_rules)
            ctoken = CondeToken(self.client)

            # Refresh token X in X minutes | Atualiza token de sessão de X em X minutos
            thr_main = Thread(target=ctoken.refresh_token)
            thr_main.start()
            # pre-sync: clear table and update data | pre-sync: limpa tabela e atualiza dados
            slocal.pre_sync()
            sremote.pre_sync()
            # synchronize | efetua o sincronismo
            slocal.sync()
            sremote.sync()
        except Exception as err:
            print(str(err))
            os._exit(0)
