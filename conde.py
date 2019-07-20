# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""Read config file and start sync.

__author__ = Jackson Lopes
__email__  = jacksonlopes@gmail.com
__url__    = https://jslabs.cc
__src__    = https://github.com/jacksonlopes/condedrive
"""
import os
import configparser
import logging
import logging.handlers
from condeconstants import CondeConstants
from condedrive import CondeDrive

class Conde(object):
    """Main class."""
    LOG_FILE           = ""
    FILE_LOG_DEBUG     = ""
    CLIENT_SECRET     = None
    CLIENT_ID         = None
    DIR_SYNC          = None
    DIR_RULES         = {}
    FILE_RULES        = {}
    log               = None

    def __init__(self):
        from condesql import CondeSql
        CondeSql()

    def start_process(self):
        """Start process. Main method.
           
           Args:
             None
           Returns:
             None
        """
        self.set_config()
        self.set_file_log()
        self.log.info("")
        self.log.info("****************************************")
        self.log.info("Init condedrive...")
        self.log.info("****************************************")
        os.system("notify-send condedrive 'Init SYNC condedrive...'")
        cmain = CondeDrive(CondeConstants().REDIRECT_URI, self.CLIENT_SECRET, self.CLIENT_ID, CondeConstants().SCOPES)
        cmain.authenticate()
        cmain.sync(self.DIR_SYNC, self.DIR_RULES, self.FILE_RULES)
        self.log.info("****** \o/ END \o/ ******")
        os.system("notify-send condedrive 'End SYNC condedrive...'")

    def set_config(self):
        """Read file config (condedrive.conf) and set variables.
           
           Args:
             None
           Returns:
             None
        """
        config = configparser.ConfigParser()
        #http://stackoverflow.com/questions/19359556/configparser-reads-capital-keys-and-make-them-lower-case
        # default ConfigParser convert lowercase
        # Resumindo: o padrao do ConfigParser é converter o nome para minusculo, por causa do Windows.        
        config.optionxform = str        
        config.read(CondeConstants().FILE_CONFIG)
        self.check_config(config)
        try:
            self.CLIENT_SECRET = config["LOGIN"]["client_secret"]
            self.CLIENT_ID = config["LOGIN"]["client_id"]
            self.LOG_FILE = config["LOG"]["filename"]
            self.FILE_LOG_DEBUG = config["LOG"]["filename_debug"]
            self.DIR_SYNC = []
            self.DIR_RULES["only_onedrive"] = [x.strip() for x in config["DIRECTORIES_RULES"]["only_onedrive"].split(',')]
            self.DIR_RULES["only_local"] = [x.strip() for x in config["DIRECTORIES_RULES"]["only_local"].split(',')]
            self.FILE_RULES["only_onedrive"] = [x.strip() for x in config["FILES_RULES"]["only_onedrive"].split(',')]
            self.FILE_RULES["only_local"] = [x.strip() for x in config["FILES_RULES"]["only_local"].split(',')]            
            # Create array: [{'/home/jsl/imagens/teste_conde': 'Pictures/teste_conde'}]
            # local directory : remote directory
            # Cria um array na forma: [{'/home/jsl/imagens/teste_conde': 'Pictures/teste_conde'}]
            # ou seja, diretorio local : diretorio remoto
            for dirconf in config["SYNC_DIR_LOCAL_X_ONEDRIVE"]:
                self.DIR_SYNC.append({dirconf:config["SYNC_DIR_LOCAL_X_ONEDRIVE"][dirconf]})
            self.check_config_read()
        except:
            print("Error in condedrive.conf")
            os._exit(1)

    def check_config_read(self):
        """Check for values in variables

           Args:
             None
           Returns:
             None
        """
        if self.CLIENT_ID is None or self.CLIENT_SECRET is None or self.LOG_FILE is None \
         or self.FILE_LOG_DEBUG is None or len(self.DIR_SYNC) == 0:
         print("Error in condedrive.conf. Value empty.")
         os._exit(1)

    def check_config(self, config):
        """Validade config info.
           
           Args:
             None
           Returns:
             None
        """
        self.print_msg_config("LOGIN->client_secret") if not config.has_option("LOGIN", "client_secret") else None
        self.print_msg_config("LOGIN->client_id") if not config.has_option("LOGIN", "client_id") else None
        self.print_msg_config("LOG->filename") if not config.has_option("LOG", "filename") else None
        self.print_msg_config("LOG->filename_debug") if not config.has_option("LOG", "filename_debug") else None

    def print_msg_config(self,field):
        """Print to stdout.
           
           Args:
             None
           Returns:
             None
        """
        print("condedrive.conf: Field not found > " + field)

    def set_file_log(self):
        """Set log file.
           
           Args:
             None
           Returns:
             None
        """
        logging.basicConfig(filename=self.FILE_LOG_DEBUG,
                            datefmt="[%Y-%m-%d %H:%M]",
                            format="%(asctime)s - %(name)-2s %(levelname)-2s %(message)s",
                            filemode='a',
                            level=logging.DEBUG)

        self.log = logging.getLogger(CondeConstants().LOGGER_NAME)
        formatter = logging.Formatter("%(asctime)s - %(funcName)35s() - %(levelname)-2s %(message)s",datefmt="[%Y-%m-%d %H:%M]")
        fhlog = logging.FileHandler(self.LOG_FILE)
        fhlog.setFormatter(formatter)
        fhlog.setLevel(logging.INFO)
        self.log.addHandler(fhlog)

if __name__ == "__main__":
    conde_init = Conde()
    conde_init.start_process()
    os._exit(0)
