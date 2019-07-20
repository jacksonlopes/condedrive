# -*- coding: utf-8 -*-
"""Utils methods local.

__author__ = Jackson Lopes
__email__  = jacksonlopes@gmail.com
__url__    = https://jslabs.cc
__src__    = https://github.com/jacksonlopes/condedrive
"""
import os
import time
import hashlib
import logging
from math import trunc
from stat import ST_INO
from datetime import datetime
from datetime import timedelta
from condesql import CondeSql
from condeconstants import CondeConstants
from condeonedriveutils import CondeOnedriveUtils
from condesqlremote import CondeSqlRemote

class CondeUtils(object):
    """Class for utils methods local."""
    csql = None
    log  = logging.getLogger(CondeConstants().LOGGER_NAME)

    def __init__(self):
        self.csql = CondeSql()

    def print_check_rules(self,str_info,str_check,ldir):
        """Print info progress:

           Args:
             str_info (str): str information
             str_check (str): string to check
             ldir (list): list strings
           Returns:
             None
        """
        if str_check not in ldir:
            self.log.info(str_info + str_check)        

    def print_info_perc(self,path,counter_pos,size_items):
        """Print info progress:

           Args:
             counter_pos (int): position
             size_items (int): total elements
           Returns:
             None
        """
        perc = round(counter_pos * 100 / size_items,2)
        if perc % 10 == 0 or counter_pos == size_items -1:
            if counter_pos == size_items -1:
                perc = 100.0
            self.log.info("* " + path + " - " + str(perc) + "%")

    def get_list_files_in_hierarchy(self, path_origin):
        """Create hash in format:
           hash[nome_diretorio] = {nome_arquivo : [data_criação,data_alteração,sha1,version]}
           hash[nome_diretorio_subdiretorio] = {nome_arquivo : [data_criação,data_alteração,sha1,version]}

           Args:
             path_origin (str): path
           Returns:
           (hash) hash files
        """
        hash_dir = {}
        for path, dirs, files in os.walk(path_origin):
            self.log.info("*** " + path)
            hash_dir[path] = {}
            counter_pos = 0

            for f in files:
                counter_pos += 1
                self.print_info_perc(path,counter_pos,len(files))
                info_arq = hash_dir[path]
                info_arq[f] = []
                info_arq[f].append(self.get_create_file_datetime(os.path.join(path, f)))
                info_arq[f].append(self.get_alter_file_datetime(os.path.join(path, f)))

                version, sha1 = self.check_file_modified_in_table_local(os.path.join(path, f))
                if version is None:
                    info_arq[f].append(self.calculate_sha1_file(os.path.join(path, f)))
                    info_arq[f].append(self.get_version_file_or_dir(os.path.join(path, f)))
                else:
                    info_arq[f].append(sha1)
                    info_arq[f].append(version)
                hash_dir[path] = info_arq
        return hash_dir

    def check_file_modified_in_table_local(self, path_file):
        """Check if file modified in table local.

           Args:
             path_file (str): path file
           Returns:
           (str) version sha1
        """
        path = os.path.dirname(path_file)
        filename = path_file[len(path)+1:]
        sql = "SELECT * FROM conde_info_local WHERE name = ? and path_local = ? and version = ?"
        values = (filename, path, self.get_version_file_or_dir(path_file))
        ret = self.csql.execute_sql(sql, values)
        if len(ret) > 0:
            return ret[0][2], ret[0][8] # version , sha1
        return None, None

    def get_create_file_datetime(self, path):
        """Get create datetime file.

           Args:
             path (str): path file
           Returns:
           (datetime) datetime file
        """
        mtime_local = os.path.getatime(path)
        return datetime.fromtimestamp(mtime_local)

    def get_alter_file_datetime(self, path):
        """Get alter datetime file.

           Args:
             path (str): path file
           Returns:
           (datetime) datetime file
        """
        mtime_local = os.path.getctime(path)
        return datetime.fromtimestamp(mtime_local)

    def calculate_sha1_file(self, path_file):
        """Get sha1 file.

           Args:
             path_file (str): path file
           Returns:
             (str) sha1
        """
        #thanks per chunk file: http://stackoverflow.com/questions/22058048/hashing-a-file-in-python
        sha1 = hashlib.sha1()
        with open(path_file, "rb") as f:
            while True:
                data = f.read(CondeConstants().SIZE_BUFFER_SHA1)
                if not data:
                    break
                sha1.update(data)
        return sha1.hexdigest().upper()

    def get_version_file_or_dir(self, path_file):
        """Get INODE file.

           Args:
             path_file (str): path file
           Returns:
             (str) inode
        """
        return str(os.stat(path_file)[ST_INO])

    def convert_hash_local_files_to_update(self, list_dir, dir_root, name_dir_in_onedrive):
        """Convert hash local (get_list_files_in_hierarchy() to update instruction.

           Args:
             list_dir (list): list directory
             dir_root (str): dir root
             name_dir_in_onedrive (str): name of dir
           Returns: 
             (tuple) sql insert/update
        """
        list_sql_insert = []
        list_sql_update = []
        for v_dir in list_dir:
            # v_dir - chave.: /home/jsl/Imagens/sobrinhos/alegre
            name = None
            version = self.get_version_file_or_dir(v_dir)
            path_local = v_dir
            # TESTE/de/FOTOS/dir01/subdir/supernovosubdir
            if v_dir[len(dir_root)+1:] != "":
                path_onedrive = name_dir_in_onedrive + '/' + v_dir[len(dir_root)+1:]
                name = v_dir[len(dir_root)+1:]
            else:
                path_onedrive = name_dir_in_onedrive
            type_item = 1 # directory | diretorio
            sha1 = None
            dt_created = self.get_create_file_datetime(path_local)
            dt_modified = self.get_alter_file_datetime(path_local)

            # if exists in table.. update | Se a versão existe na tabela.. gera UPDATE.. senão INSERT
            sql = "SELECT * from conde_info_local WHERE version = " + version
            if len(self.csql.execute_sql(sql, None)) == 0:
                # not exists.. insert | Não existe, INSERT
                list_sql_insert.append((name, version, path_local, path_onedrive, type_item, sha1, dt_created, dt_modified))
            else:
                list_sql_update.append([name, version, path_local, path_onedrive, type_item, None, None, sha1, dt_created, dt_modified])

            # files, if exist | Arquivos, se existir.
            for name_arq in list_dir[v_dir].keys():
                version = self.get_version_file_or_dir(v_dir + '/' + name_arq)
                type_item = 2 # file | arquivo
                sha1 = list_dir[v_dir][name_arq][2]
                dt_created = list_dir[v_dir][name_arq][0]
                dt_modified = list_dir[v_dir][name_arq][1]

                sql = "SELECT * from conde_info_local WHERE version = " + version
                if len(self.csql.execute_sql(sql, None)) == 0:
                    # INSERT
                    list_sql_insert.append((name_arq, version, path_local, path_onedrive, type_item, sha1, dt_created, dt_modified))
                else:
                    list_sql_update.append([name_arq, version, path_local, path_onedrive, type_item, None, None, sha1, dt_created,dt_modified])

        return list_sql_insert, list_sql_update

    def convert_hash_onedrive_files_to_up(self, client, key_root, path_local, item_root, list_items):
        """Convert hash onedrive to update/insert sql instruction.

           Args:
             client (Client): client onedrive
             key_root (str): key root dir onedrive
             path_local (str): path local
             item_root (Item): item root onedrive
             list_items (list): list items onedrive
           Returns:
             (tuple) sql insert/update
        """
        codutils = CondeOnedriveUtils(client)
        list_sql_insert = []
        list_sql_update = []
        list_versions = []
        counter = 0
        counter_pos = 0
        csqlremote = CondeSqlRemote()
        size_items = len(list_items)
        for item in list_items:

            counter_pos += 1
            self.print_info_perc(path_local,counter_pos,size_items)
            # get full path...
            # Tenho que obter o caminho completo ate o arquivo, ou seja, até o pai.
            # str_hier_dir -- TESTE/de/FOTOS/alegre
            exists_in_table = False
            version_tb = None
            id_onedrive = item.id
            id_father_onedrive = item.parent_reference.id

            if counter == 50:
                counter = 0
                client.auth_provider.refresh_token()

            counter += 1
            sql = "SELECT * from conde_info_onedrive WHERE "
            sql += " id_onedrive = '" + id_onedrive + "' AND id_father_onedrive = '" + id_father_onedrive + "'"
            ret = self.csql.execute_sql(sql, None)
            if len(ret) == 0:
                # not exist | Nao existe
                list_hier = codutils.get_hierarchy_dir_item(item_root, item)
            else:
                exists_in_table = True
                version_tb = ret[0][2]
                name_split = ret[0][1].split('/')

                if len(name_split) == 0:
                    name_split = None
                if len(name_split) == 1:
                    name_split = ret[0][1]
                elif len(name_split) > 1:
                    name_split = ret[0][1].split('/')[-1:][0]

                if (not name_split is None) and isinstance(name_split, str) and name_split == item.name:
                    if ret[0][5] == 2: # file | arquivo
                        path_db = ret[0][4] + '/' + name_split
                        list_hier = path_db.split('/')
                        for r_inx in range(0, len(key_root.split('/'))):
                            if len(list_hier) == 0:
                                break
                    else:
                        list_hier = codutils.get_hierarchy_dir_item(item_root, item)
                else:
                    list_hier = codutils.get_hierarchy_dir_item(item_root, item)

            name = ""
            type_item = self.get_type_item(item)
            path_onedrive = self.convert_list_to_str(list_hier, '/')
            dt_created = item.created_date_time
            dt_modified = item.last_modified_date_time

            if len(list_hier) > 1:
                path_local_dir = path_local + '/' + path_onedrive[len(key_root)+1:]
            else:
                path_local_dir = path_local

            # if directory in root but not root | caso diretorio esteja na raiz mas não seja a raiz.
            if item.id != item_root.id and len(list_hier) == 1:
                path_local_dir = path_local + '/' + item.name
            
            version = None
            sha1 = None
            if type_item == 1: # directory | diretorio
                name = path_onedrive[len(key_root) + 1:]
                if self.check_exists_path(path_local_dir) == True:
                    version = self.get_version_file_or_dir(path_local_dir)
            else:
                sha1 = self.get_sha1_item(item)
                name = item.name
                if self.check_exists_path(path_local_dir) == True:
                    version = self.get_version_file_or_dir(path_local_dir)
                # cut name in path | retira name do path_local e path_onedrive
                path_local_dir = os.path.dirname(path_local_dir)
                path_onedrive = os.path.dirname(path_onedrive)

            if version != None and version in list_versions:
                continue
            # if version in table.. insert.. else update | Se a versão existe na tabela.. gera UPDATE.. senão INSERT
            if exists_in_table is False:
                list_sql_insert.append((name, version, path_local_dir, path_onedrive, type_item, id_onedrive, id_father_onedrive, sha1, dt_created, dt_modified))
            else:
                version = version_tb
                list_sql_update.append([name, version, path_local_dir, path_onedrive, type_item, id_onedrive, id_father_onedrive, sha1, dt_created, dt_modified])

            list_versions.append(version)

            if counter == 15:
                csqlremote.update_remote_table_conde(list_sql_insert, list_sql_update)
                list_sql_insert = []
                list_sql_update = []

        csqlremote.update_remote_table_conde(list_sql_insert, list_sql_update)

    def get_type_item(self, item):
        """Get type of item.

           Args:
             item (Item): item onedrive
           Returns:
             (int) 1 - directory , 2 - file
        """
        if item.folder != None:
            return 1
        else:
            return 2

    def get_sha1_item(self, item):
        """Get sha1 of item.

           Args:
             item (Item): item onedrive
           Returns:
             (str) sha1 if file
        """
        if self.get_type_item(item) == 2:
            return item.file.hashes.sha1_hash
        else:
            return None

    def convert_list_to_str(self, list_info, delimiter):
        """Convert list to str (with delimiter).

           Args:
             list_info (list): list directory
             delimiter (str): delimiter
           Returns:
             (str) path
        """
        str_final = ""
        for str_list in list_info:
            str_final += str_list + delimiter
        return str_final[:len(str_final)-1]

    def chech_file_more_current(self, path_file_local, item_datetime):
        """Verify file more current.

           Args:
             path_file_local (str): path local file
             item_datetime (datetime): item datetime
           Returns:
             (int) 1 - local , 2 - onedrive
        """
        # local file | rquivo local
        if isinstance(path_file_local, str):
            mtime_local = os.path.getctime(path_file_local)
            data_mod_local = datetime.fromtimestamp(mtime_local)
        else:
            data_mod_local = path_file_local
        # onedrive file | Arquivo remoto
        data_real_file_remote = item_datetime - timedelta(hours=self.get_diff_timezone_utc())

        if data_mod_local > data_real_file_remote:
            return 1
        else:
            return 2

    def get_diff_timezone_utc(self):
        """Get diff timezone local with UTC.

           Args:
             None
           Returns:
             (int) diff timezone with UTC
        """
        # credits: http://stackoverflow.com/a/10854983
        offset = time.timezone if (time.localtime().tm_isdst == 0) else time.altzone
        return offset / 60 / 60

    def rename_local_item(self, source, destiny):
        """Rename local file/dir.

           Args:
             source (str): source
             destiny (str): destiny
           Returns:
             None
        """
        os.rename(source, destiny)

    def renames_local_item(self, source, destiny):
        """Rename recursive local file/dir.

           Args:
             source (str): source
             destiny (str): destiny
           Returns:
             None
        """
        os.renames(source, destiny)

    def check_exists_path(self, path):
        """Check if exists path.

           Args:
             path (str): path
           Returns:
             (Boolean) True exists , False not exists
        """
        return os.path.exists(path)

    def check_exists_in_rules(self, rules, path):
        """Check if path exists in rules.

           Args:
             rules (list): list rules
             path (str): path
           Returns:
             (Boolean) True exists , False not exists
        """
        for rule_str in rules:
            if rule_str in path:
                return True
        return False
