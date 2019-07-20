# -*- coding: utf-8 -*-
"""Refresh token onedrive.

__author__ = Jackson Lopes
__email__  = jacksonlopes@gmail.com
__url__    = https://jslabs.cc
__src__    = https://github.com/jacksonlopes/condedrive
"""
import time
from singleton import Singleton
from condesql import CondeSql
from condeconstants import CondeConstants

class CondeToken(metaclass=Singleton):
    """Class for refresh token."""
    client       = None
    csql         = None

    def __init__(self, client):
        self.client = client
        self.csql = CondeSql()

    def refresh_token(self):
        """Refresh token X in X minutes.

           Args:
             None
           Returns:
             None
        """
        while True:
            time.sleep(CondeConstants().TIME_GET_NEW_TOKEN * 60)
            self.client.auth_provider.refresh_token()
            self.client.auth_provider.save_session()
