# -*- coding: utf-8 -*-
"""Sync onedrive => local.

__author__ = Jackson Lopes
__email__  = jacksonlopes@gmail.com
__url__    = https://jslabs.cc
__src__    = https://github.com/jacksonlopes/condedrive
"""
import os
import logging
import onedrivesdk
import threading
from stat import *
from datetime import datetime
from onedrivesdk.helpers import GetAuthCodeServer
from PIL import Image
from condeconstants import CondeConstants
from condesql import CondeSql
from condeutils import CondeUtils
from condeonedriveutils import CondeOnedriveUtils
from condesqlremote import CondeSqlRemote

class CondeSyncRemote(object):
    """Class for sync onedrive => local."""
    log        = logging.getLogger(CondeConstants().LOGGER_NAME)
    client     = None
    csql       = None
    cutils     = None
    codutils   = None
    csqlremote = None
    dir_sync   = None
    dir_rules  = None
    file_rules = None    

    def __init__(self, client, dir_sync, dir_rules, file_rules):
        self.client = client
        self.csql = CondeSql()
        self.cutils = CondeUtils()
        self.codutils = CondeOnedriveUtils(self.client)
        self.csqlremote = CondeSqlRemote()
        self.dir_sync = dir_sync
        self.dir_rules = dir_rules
        self.file_rules = file_rules

    def pre_sync(self):
        """Call enter_hierarchy_directory_onedrive.

           Args:
             None
           Returns:
             None
        """
        self.enter_hierarchy_directory_onedrive()

    def enter_hierarchy_directory_onedrive(self):
        """Update (in table) info dir/files onedrive.

           Args:
             None
           Returns:
             None
        """
        self.log.info("* UP 'conde_info_onedrive'")
        lst_threads = []
        for v_dir in self.dir_sync:
            for name in v_dir.keys():
                # v_dir[name] => 'TESTE/de/FOTOS'
                #self.log.info("*** " + v_dir[name])
                t = threading.Thread(target=self.convert_hash_onedrive, args=(v_dir[name],name,))
                lst_threads.append(t)
                #item_root = self.codutils.enter_hierarchy_directory_onedrive(v_dir[name], CondeConstants().DEFAULT_ONEDRIVE_DIR)
                #self.cutils.convert_hash_onedrive_files_to_up(self.client, v_dir[name], name, item_root, self.codutils.get_all_list_items(item_root))
        for st in lst_threads:
            st.start()
        for st in lst_threads:
            st.join()

    def convert_hash_onedrive(self,v_dir_name,name):
        self.log.info("*** " + v_dir_name)
        item_root = self.codutils.enter_hierarchy_directory_onedrive(v_dir_name, CondeConstants().DEFAULT_ONEDRIVE_DIR)
        self.cutils.convert_hash_onedrive_files_to_up(self.client, v_dir_name, name, item_root, self.codutils.get_all_list_items(item_root))

    def sync(self):
        """Call sync_onedrive_to_local.

           Args:
             None
           Returns:
             None
        """
        self.log.info("--------------------------------")
        self.log.info("*** [SYNC ONEDRIVE => LOCAL] ***")
        self.sync_onedrive_to_local()

    def sync_onedrive_to_local(self):
        """Sync onedrive -> local.

           Args:
             None
           Returns:
             None
        """
        # 1o. Directories | 1o. Diretorios
        self.sync_onedrivedir_to_local()
        # 2o. Files | 2o. Arquivos
        self.sync_onedrivefiles_to_local()

    def sync_onedrivedir_to_local(self):
        """Sync structure directory onedrive -> local.

           Args:
             None
           Returns:
             None
        """
        self.log.info("* SYNC dir")

        # Directories that have been created | Diretorios que foram criados
        sql = "SELECT co.* FROM conde_info_onedrive co "
        sql += "WHERE co.type = 1 AND co.version IS NULL "
        sql += " AND id_onedrive NOT IN (SELECT id_onedrive FROM conde_info_local WHERE id_onedrive IS NOT NULL) "
        odir_created = self.csql.execute_sql(sql, None)

        # Directories that have been renamed | Diretorios que foram renomeados
        sql = "SELECT co.* FROM conde_info_onedrive co, conde_info_local cl WHERE "
        sql += " co.type = 1 AND co.version = cl.version AND co.path_local <> cl.path_local "
        sql += " ORDER BY co.path_local DESC"
        odir_renamed = self.csql.execute_sql(sql, None)

        self.sync_onedrivedir_created(odir_created)
        self.sync_onedrivedir_renamed(odir_renamed)

    def sync_onedrivedir_created(self, odir_created):
        """Update directory created onedrive -> local.

           Args:
             ldir_created (list): list directory created
           Returns:
             None
        """
        lpr_rules = []
        self.log.info("* No. directories created: " + str(len(odir_created)))
        for odir in odir_created:

            if self.cutils.check_exists_in_rules(self.dir_rules["only_onedrive"], odir[4]):                
                self.cutils.print_check_rules("** keep directory only in onedrive: ",odir[4],lpr_rules)
                lpr_rules.append(odir[4])
                continue

            self.log.info("** creating directory in LOCAL: " + odir[3])
            if not os.path.exists(odir[3]):
                # creates hierarchy in filesystem | cria hierarquia no filesystem
                os.makedirs(odir[3])

                version = self.cutils.get_version_file_or_dir(odir[3])
                try:
                    dt_created = datetime.strptime(odir[9], "%Y-%m-%d %H:%M:%S.%f")
                except ValueError:
                    dt_created = datetime.strptime(odir[9], "%Y-%m-%d %H:%M:%S")
                
                try:
                    dt_modified = datetime.strptime(odir[10], "%Y-%m-%d %H:%M:%S.%f")
                except ValueError:
                    dt_modified = datetime.strptime(odir[10], "%Y-%m-%d %H:%M:%S")

                values = (None, version, odir[3], odir[4], 1, odir[6], odir[7], None, dt_created, dt_modified)
                # insert in table | insere registro na tabela local
                self.csql.insert_in_table("conde_info_local", values)
                # update version in table | atualiza version na tab. onedrive
                self.csqlremote.update_version_onedrive(version, odir[6], odir[7])

    def sync_onedrivedir_renamed(self, odir_renamed):
        """Update directory renamed onedrive -> local.

           Args:
             ldir_renamed (list): list directory renamed
           Returns:
             None
        """
        lpr_rules = []
        self.log.info("* No. renamed directories: " + str(len(odir_renamed)))
        for odir in odir_renamed:

            if self.cutils.check_exists_in_rules(self.dir_rules["only_onedrive"], odir[4]):                
                self.cutils.print_check_rules("** keep directory only in onedrive: ",odir[4],lpr_rules)
                lpr_rules.append(odir[4])
                continue

            # get registry in table | Obtenho registro na tabela local
            sql = "SELECT * FROM conde_info_local WHERE version = " + odir[2]
            ldir = self.csql.execute_sql(sql,None)

            dt_modified_onedrive = datetime.strptime(odir[10], "%Y-%m-%d %H:%M:%S.%f")
            old_path_local       = ldir[0][3]
            old_path_onedrive    = ldir[0][4]
            new_path_local       = odir[3]
            new_path_onedrive    = odir[4]
            old_version          = odir[2]
            new_version          = None

            if self.cutils.check_exists_path(new_path_local) == True:
                new_version = self.cutils.get_version_file_or_dir(new_path_local)
                self.csqlremote.update_versions_local_onedrive(new_version, old_version)
                self.csql.normalize_paths_hierarchy(new_path_local, old_path_local, new_path_onedrive, old_path_onedrive)
                continue

            # if datetime local most current, keep.. adjusted in sync local...
            # se mais atual localmente, deixo para a sincronização local...
            if self.cutils.chech_file_more_current(ldir[0][3], dt_modified_onedrive) == 1:
                continue

            self.log.info("** renaming directory: " + old_path_local + " => " + new_path_local)
            self.cutils.renames_local_item(old_path_local, new_path_local)
            new_version = self.cutils.get_version_file_or_dir(new_path_local)

            self.csqlremote.update_versions_local_onedrive(new_version, old_version)
            self.csql.normalize_paths_hierarchy(new_path_local, old_path_local, new_path_onedrive, old_path_onedrive)

    def sync_onedrivefiles_to_local(self):
        """Sync files onedrive -> local.

           Args:
             None
           Returns:
             None
        """
        self.log.info("* SYNC arq")
        # created files | Arquivos que foram criados.
        sql = "SELECT * FROM conde_info_onedrive co "
        sql += "WHERE co.type = 2 and version IS NULL "
        files_created = self.csql.execute_sql(sql, None)

        # renamed files | Arquivos que foram renomeados
        sql = "SELECT co.* FROM conde_info_onedrive co , conde_info_local cl WHERE "
        sql += "co.type = 2 AND co.version = cl.version AND co.name <> cl.name "
        sql += " AND cl.sha1 = co.sha1"
        files_renamed = self.csql.execute_sql(sql, None)

        # change files | Arquivos que foram alterados
        sql = "SELECT co.* FROM conde_info_onedrive co , conde_info_local cl WHERE "
        sql += "co.type = 2 AND co.version = cl.version AND co.name = cl.name "
        sql += " AND cl.sha1 <> co.sha1"
        files_modified = self.csql.execute_sql(sql, None)

        self.sync_onedrivefiles_created(files_created)
        self.sync_onedrivefiles_renamed(files_renamed)
        self.sync_onedrivefiles_modified(files_modified)

    def sync_onedrivefiles_created(self, files_created):
        """Update files created onedrive -> local.

           Args:
             files_created (list): list files created
           Returns:
             None
        """
        lpr_rules = []
        self.log.info("* No. files created/updated: " + str(len(files_created)))        
        for o_drive in files_created:
            name                = o_drive[1]
            version             = o_drive[2]
            path_local          = o_drive[3]
            path_onedrive       = o_drive[4]
            id_onedrive         = o_drive[6]
            id_father_onedrive  = o_drive[7]
            sha1                = o_drive[8]
            try:
                dt_created = datetime.strptime(o_drive[9], "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                dt_created = datetime.strptime(o_drive[9], "%Y-%m-%d %H:%M:%S")
            
            try:
                dt_modified = datetime.strptime(o_drive[10], "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                dt_modified = datetime.strptime(o_drive[10], "%Y-%m-%d %H:%M:%S")

            if self.cutils.check_exists_in_rules(self.dir_rules["only_onedrive"], path_onedrive):                
                self.cutils.print_check_rules("** keep directory only in onedrive: ",path_onedrive,lpr_rules)
                lpr_rules.append(path_onedrive)
                continue

            self.log.info("** down file: " + path_local + '/' + name)
            item = self.codutils.get_item_by_id(id_onedrive)
            if self.codutils.download(item, path_local, name) == False:
                self.log.info("** ERROR down file: " + path_local + '/' + name)
                continue
            version = self.cutils.get_version_file_or_dir(path_local + '/' + name)

            # insert in conde_info_local and up and onedrive | Inserir na tabela conde_info_local e atualizar na onedrive
            values = (name, version, path_local, path_onedrive, 2, str(item.id), str(item.parent_reference.id), sha1, item.created_date_time, item.last_modified_date_time)
            self.csql.insert_in_table("conde_info_local", values)
            self.csqlremote.update_version_onedrive(version, str(item.id), str(item.parent_reference.id))

    def sync_onedrivefiles_renamed(self, files_renamed):
        """Update files renamed onedrive -> local.

           Args:
             files_renamed (list): list files renamed
           Returns:
             None
        """
        lpr_rules = []
        self.log.info("* No. renamed files: " + str(len(files_renamed)))
        for o_drive in files_renamed:
            name          = o_drive[1]
            version       = o_drive[2]
            path_local    = o_drive[3]
            path_onedrive = o_drive[4]
            id_onedrive   = o_drive[6]
            sha1          = o_drive[8]
            dt_modified   = o_drive[10]

            if self.cutils.check_exists_in_rules(self.dir_rules["only_onedrive"], path_onedrive):                
                self.cutils.print_check_rules("** keep directory only in onedrive: ",path_onedrive,lpr_rules)
                lpr_rules.append(path_onedrive)
                continue

            # get data | Obtém dados local
            sql = "SELECT * FROM conde_info_local WHERE version = " + version
            f_local = self.csql.execute_sql(sql, None)

            # If format: %Y-%m-%d %H:%M:%S | se formato...
            if len(dt_modified) == 19:
                dt_modified = dt_modified + ".00"
            dt_modified = datetime.strptime(dt_modified, "%Y-%m-%d %H:%M:%S.%f")
            new_path_local = path_local + '/' + name
            old_path_local = path_local + '/' + f_local[0][1]
            if self.cutils.chech_file_more_current(old_path_local, dt_modified) == 1:
                continue

            self.log.info("** renaming file: " + old_path_local + " => " + new_path_local)
            self.cutils.rename_local_item(old_path_local, new_path_local)
            # update in onedrive table with new name | Atualiza tabela onedrive com o novo nome
            self.csql.update_name_table("conde_info_local", version, name)

    def sync_onedrivefiles_modified(self, files_modified):
        """Update files modified onedrive -> local.

           Args:
             files_modified (list): list files modified
           Returns:
             None
        """
        lpr_rules = []
        self.log.info("* No. altered files: " + str(len(files_modified)))
        for o_drive in files_modified:
            name          = o_drive[1]
            version       = o_drive[2]
            path_local    = o_drive[3]
            path_onedrive = o_drive[4]
            id_onedrive   = o_drive[6]
            sha1          = o_drive[8]
            dt_modified   = o_drive[10]

            if self.cutils.check_exists_in_rules(self.dir_rules["only_onedrive"], path_onedrive):                
                self.cutils.print_check_rules("** keep directory only in onedrive: ",path_onedrive,lpr_rules)
                lpr_rules.append(path_onedrive)
                continue

            dt_modified = datetime.strptime(dt_modified, "%Y-%m-%d %H:%M:%S.%f")
            if self.cutils.chech_file_more_current(path_local + '/' + name, dt_modified) == 1:
                continue

            self.log.info("** down file: " + path_local + '/' + name)
            item = self.codutils.get_item_by_id(id_onedrive)
            if self.codutils.download(item, path_local, name) == False:
                self.log.info("** ERROR down file: " + path_local + '/' + name)
                continue
            new_version = self.cutils.get_version_file_or_dir(path_local + '/' + name)

            # update in tables with new version | Atualiza tabelas com nova version
            self.csqlremote.update_versions_local_onedrive(new_version, version)
            
