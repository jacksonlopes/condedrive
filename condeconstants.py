# -*- coding: utf-8 -*-
"""Constants for program.

__author__ = Jackson Lopes
__email__  = jacksonlopes@gmail.com
"""
class CondeConstants(object):
    """Class constants."""

    FILE_CONFIG = "condedrive.conf"
    REDIRECT_URI = "http://localhost:8080/"
    API_BASE_URL = "https://api.onedrive.com/v1.0/"
    SCOPES = ["wl.signin", "wl.offline_access", "onedrive.readwrite"]
    LOGGER_NAME = "condeLog"
    NAME_DATABASE = "dbase/conde.db"

    DEFAULT_ONEDRIVE_DIR = "root"
    MAX_SINGLE_FILE_UPLOAD = 100 * 1024 * 1024

    TIME_GET_NEW_TOKEN = 10
    SIZE_BUFFER_SHA1 = 512000

