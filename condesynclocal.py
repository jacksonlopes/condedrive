# -*- coding: utf-8 -*-
"""Sync local => onedrive.

__author__ = Jackson Lopes
__email__  = jacksonlopes@gmail.com
__url__    = https://jslabs.cc
__src__    = https://github.com/jacksonlopes/condedrive
"""
import os
import logging
import onedrivesdk
from onedrivesdk.helpers import GetAuthCodeServer
from PIL import Image
from datetime import datetime
from condeconstants import CondeConstants
from condesql import CondeSql
from condeutils import CondeUtils
from condeonedriveutils import CondeOnedriveUtils
from condesyncremote import CondeSyncRemote
from condesqllocal import CondeSqlLocal

class CondeSyncLocal(object):
    """Class for sync local => onedrive."""
    log        = logging.getLogger(CondeConstants().LOGGER_NAME)
    client     = None
    csql       = None
    cutils     = None
    codutils   = None
    csqllocal  = None    
    dir_sync   = None
    dir_rules  = None
    file_rules = None

    def __init__(self, client, dir_sync, dir_rules, file_rules):
        self.client = client
        self.csql = CondeSql()
        self.cutils = CondeUtils()
        self.codutils = CondeOnedriveUtils(self.client)
        self.csqllocal = CondeSqlLocal()
        self.dir_sync = dir_sync
        self.dir_rules = dir_rules
        self.file_rules = file_rules

    def pre_sync(self):
        """Call update_local_table.

           Args:
             None
           Returns:
             None
        """
        self.update_local_table()

    def update_local_table(self):
        """Update table conde_info_local.

           Args:
             None
           Returns:
             None
        """
        self.log.info("* UP 'conde_info_local'")
        # [{'/home/jsl/Imagens/sobrinhos': 'TESTE/de/FOTOS'}]
        for v_dir in self.dir_sync:
            # v_dir - [{'/home/jsl/Imagens/sobrinhos': 'TESTE/de/FOTOS'}]
            # /home/jsl/Imagens/sobrinhos
            name_dir_local = list(v_dir.keys())[0]
            # TESTE/de/FOTOS
            name_dir_in_onedrive = v_dir[name_dir_local]
            list_dir = self.cutils.get_list_files_in_hierarchy(name_dir_local)
            # convert hash files to update
            # converte hash de arquivos para update
            list_insert, list_update = self.cutils.convert_hash_local_files_to_update(list_dir, name_dir_local, name_dir_in_onedrive)
            self.csqllocal.update_local_table_conde(list_insert, list_update)

    def sync(self):
        """Init sync files.

           Args:
             None
           Returns:
             None
        """
        self.log.info("--------------------------------")
        self.log.info("*** [SYNC LOCAL => ONEDRIVE] ***")
        self.normalize_tables()
        self.sync_local_to_onedrive()

    def normalize_tables(self):
        """Normalize tables.. alter create new versions.

           Args:
             None
           Returns:
             None
        """
        self.csql.normalize_tables()

    def sync_local_to_onedrive(self):
        """Sync local => onedrive.

           Args:
             None
           Returns:
             None
        """
        # 1o. Directories | 1o. Diretorios
        self.sync_localdir_to_onedrive()
        # 2o. Files | 2o. Arquivos
        self.sync_localfiles_to_onedrive()

    def sync_localdir_to_onedrive(self):
        """Sync structure directory local => onedrive.

           Args:
             None
           Returns:
             None
        """
        self.log.info("* SYNC dir")
        # Directories that have been created | Diretorios que foram criados
        sql = "SELECT cl.* FROM conde_info_local cl "
        sql += "WHERE cl.type = 1 AND cl.version NOT IN(SELECT version FROM conde_info_onedrive) "
        ldir_created = self.csql.execute_sql(sql, None)

        # Directories that have been renamed | Diretorios que foram renomeados
        sql = "SELECT cl.* FROM conde_info_local cl , conde_info_onedrive co WHERE "
        sql += "cl.type = 1 AND cl.version = co.version AND cl.path_local <> co.path_local "
        sql += " ORDER BY cl.path_local"
        ldir_renamed = self.csql.execute_sql(sql, None)

        self.sync_localdir_created(ldir_created)
        self.sync_localdir_renamed(ldir_renamed)

    def sync_localdir_created(self, ldir_created):
        """Create structure hierarchy in onedrive.

           Args:
             ldir_created (list): list directory for create
           Returns:
             None
        """
        lpr_rules = []
        self.log.info("* No. directories created: " + str(len(ldir_created)))
        for ldir in ldir_created:

            if self.cutils.check_exists_in_rules(self.dir_rules["only_local"], str(ldir[3])):                
                self.cutils.print_check_rules("** keep directory only locally: ",str(ldir[3]),lpr_rules)
                lpr_rules.append(str(ldir[3]))
                continue

            self.log.info("** creating directory in ONEDRIVE: " + str(ldir[3]))

            # ldir[4] - path_onedrive
            item = self.codutils.create_hierarchy_directory_onedrive(ldir[4], CondeConstants().DEFAULT_ONEDRIVE_DIR)
            # Insert in table conde_info_onedrive | Inserir na tabela conde_info_onedrive
            values = (None, ldir[2], ldir[3], ldir[4], 1, item.id, item.parent_reference.id, None, item.created_date_time, item.last_modified_date_time)
            self.csql.insert_in_table("conde_info_onedrive", values)
            # update id_onedrive e id_father_onedrive | Atualiza id_onedrive e id_father_onedrive na tabela local
            self.csqllocal.update_ids_local(ldir[2], str(item.id), str(item.parent_reference.id))

    def sync_localdir_renamed(self, ldir_renamed):
        """Update directory renamed local -> onedrive.

           Args:
             ldir_renamed (list): list directory renamed
           Returns:
             None
        """
        lpr_rules = []
        self.log.info("* No. renamed directories: " + str(len(ldir_renamed)))
        for ldir in ldir_renamed:

            if self.cutils.check_exists_in_rules(self.dir_rules["only_local"], str(ldir[3])):                
                self.cutils.print_check_rules("** keep directory only locally: ",str(ldir[3]),lpr_rules)
                lpr_rules.append(str(ldir[3]))
                continue

            # get registry in table | Obtenho registro na tabela onedrive
            sql = "SELECT * FROM conde_info_onedrive WHERE version = " + ldir[2]
            odir = self.csql.execute_sql(sql, None)
            # required to update in onedrive | Necessário para pode atualizar o item no onedrive
            item = self.codutils.get_item_by_id(odir[0][6])

            # update name in onedrive | Atualiza nome no onedrive
            old_path_local       = odir[0][3]
            old_path_onedrive    = odir[0][4]
            new_path_local       = ldir[3]
            new_path_onedrive    = ldir[4]

            # if datetime Onedrive most current, keep.. adjusted in sync onedrive...
            # Se a data do Item é superior a local, continuo.. isso será ajustado
            # na sincronização onedrive -> local
            if self.cutils.chech_file_more_current(ldir[3], item.last_modified_date_time) == 2:
                continue

            self.log.info("** renaming directory: " + old_path_local + " => " + new_path_local)

            name_rename = ldir[3].split('/')[len(ldir[3].split('/')) - 1]
            item = self.codutils.renamed_item(item, name_rename)
            self.csql.normalize_paths_hierarchy(new_path_local, old_path_local, new_path_onedrive, old_path_onedrive)

    def sync_localfiles_to_onedrive(self):
        """Sync files local -> onedrive.

           Args:
             None
           Returns:
             None
        """
        self.log.info("* SYNC arq")
        # Created files | Arquivos que foram criados.
        # When you rename a file it is creating another one on the onedrive 
        # because it changes the inode
        # FIXME: Quando renomeia arquivo, ele está enviando outro para o onedrive
        # isso está sendo causado apenas qdo renomeio local.. pois
        # muda o version, fica com id_onedrive e id_father_onedrive nulos
        # e a busca por nome, path n vai ter na tab. onedrive
        # Acontece qdo muda o conteudo e muda o nome do arquivo local..
        sql = "SELECT * FROM conde_info_local cl "
        sql += "WHERE cl.type = 2 and id_onedrive IS NULL and id_father_onedrive IS NULL "
        sql += "AND cl.version NOT IN(SELECT version FROM conde_info_onedrive WHERE version IS NOT NULL) "
        sql += "AND cl.name NOT IN(SELECT name FROM conde_info_onedrive WHERE name IS NOT NULL)"
        files_created = self.csql.execute_sql(sql, None)

        # Renamed files | Arquivos que foram renomeados
        sql  = "SELECT cl.* FROM conde_info_local cl , conde_info_onedrive co WHERE "
        sql += "cl.type = 2 AND cl.version = co.version AND cl.name <> co.name "
        sql += " AND cl.sha1 = co.sha1"
        files_renamed = self.csql.execute_sql(sql, None)

        # Change files | Arquivos que foram alterados
        sql = "SELECT co.* FROM conde_info_local cl , conde_info_onedrive co WHERE "
        sql += "cl.type = 2 AND cl.name = co.name AND cl.path_local = co.path_local "
        sql += " AND cl.path_onedrive = co.path_onedrive AND co.sha1 <> cl.sha1"
        files_modified = self.csql.execute_sql(sql, None)

        self.sync_localfiles_created(files_created)
        self.sync_localfiles_renamed(files_renamed)
        self.csql.normalize_tables()
        self.sync_localfiles_modified(files_modified)

    def sync_localfiles_created(self, files_created):
        """Sync files creates local -> onedrive.

           Args:
             files_created (list): list files created
           Returns:
             None
        """
        lpr_rules = []
        self.log.info("* No. files created/updated: " + str(len(files_created)))
        for f_local in files_created:
            name          = f_local[1]
            version       = f_local[2]
            path_local    = f_local[3]
            path_onedrive = f_local[4]
            sha1          = f_local[8]

            if self.cutils.check_exists_in_rules(self.dir_rules["only_local"], path_local):                
                self.cutils.print_check_rules("** keep directory only locally: ",path_local,lpr_rules)
                lpr_rules.append(path_local)
                continue

            item = self.codutils.enter_hierarchy_directory_onedrive(path_onedrive, CondeConstants().DEFAULT_ONEDRIVE_DIR)

            self.log.info("** upload file: " + path_local + '/' + name)

            # Send and get Item onedrive | Envio o arquivo e obtenho o Item correspondente ao envio
            item = self.codutils.upload(name, path_local + '/' + name, item, path_onedrive)

            # Insert in tables | Inserir na tabela conde_info_onedrive e atualizar na local
            values = (name, version, path_local, path_onedrive, 2, str(item.id), str(item.parent_reference.id), sha1, item.created_date_time, item.last_modified_date_time)
            self.csql.insert_in_table("conde_info_onedrive", values)
            self.csqllocal.update_ids_local(version, str(item.id), str(item.parent_reference.id))

    def sync_localfiles_renamed(self, files_renamed):
        """Sync files renamed local -> onedrive.

           Args:
             files_renamed (list): list files renamed
           Returns:
             None
        """
        lpr_rules = []
        self.log.info("* No. renamed files: " + str(len(files_renamed)))
        for f_local in files_renamed:
            name          = f_local[1]
            version       = f_local[2]
            path_local    = f_local[3]
            path_onedrive = f_local[4]
            sha1          = f_local[8]
            dt_modified   = f_local[10]
            id_onedrive   = f_local[6]

            if self.cutils.check_exists_in_rules(self.dir_rules["only_local"], path_local):                
                self.cutils.print_check_rules("** keep directory only locally: ",path_local,lpr_rules)
                lpr_rules.append(path_local)
                continue

            item = self.codutils.get_item_by_id(id_onedrive)
            # If format: %Y-%m-%d %H:%M:%S | Se formato estiver incompleto...
            if len(dt_modified) == 19:
                dt_modified = dt_modified + ".00"
            dt_modified = datetime.strptime(dt_modified, "%Y-%m-%d %H:%M:%S.%f")
            if self.cutils.chech_file_more_current(dt_modified, item.last_modified_date_time) == 2:
                continue

            self.log.info("** renaming file: " + str(item.name) + " => " + f_local[1])
            self.codutils.renamed_item(item, name)
            # updata name in table | Atualiza tabela onedrive com o novo nome
            self.csql.update_name_table("conde_info_onedrive", version, name)

    def sync_localfiles_modified(self, files_modified):
        """Sync files modified local -> onedrive.

           Args:
             files_modified (list): list files modified
           Returns:
             None
        """
        lpr_rules = []
        self.log.info("* No. altered files: " + str(len(files_modified)))
        for f_local in files_modified:
            name          = f_local[1]
            version       = f_local[2]
            path_local    = f_local[3]
            path_onedrive = f_local[4]
            id_onedrive   = f_local[6]
            sha1          = f_local[8]
            dt_modified   = f_local[10]

            if self.cutils.check_exists_in_rules(self.dir_rules["only_local"], path_local):                
                self.cutils.print_check_rules("** keep directory only locally: ",path_local,lpr_rules)
                lpr_rules.append(path_local)
                continue

            # get Item | Obtém Item
            sql = "SELECT * FROM conde_info_onedrive WHERE "
            sql += " name = '" + name + "' AND path_local = '" + path_local + "' "
            sql += " AND path_onedrive = '" + path_onedrive + "'"
            o_drive = self.csql.execute_sql(sql, None)

            item = self.codutils.get_item_by_id(o_drive[0][7])
            if self.cutils.chech_file_more_current(path_local + '/' + name, item.last_modified_date_time) == 2:
                continue

            self.log.info("** upload file: " + path_local + '/' + name)

            item = self.codutils.upload(name, path_local + '/' + name, item, path_onedrive)

            # update id_onedrive and id_father_onedrive | Atualiza id_onedrive e id_father_onedrive na tabela local
            self.csqllocal.update_ids_local(version, str(item.id), str(item.parent_reference.id))
            # update ... | Atualiza version,id_onedrive,id_father_onedrive,sha1 na onedrive
            self.csqllocal.update_version_sha1_onedrive(str(item.id), str(item.parent_reference.id), version, sha1)

