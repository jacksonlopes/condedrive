# -*- coding: utf-8 -*-
"""Sql methods local.

__author__ = Jackson Lopes
__email__  = jacksonlopes@gmail.com
"""
from condesql import CondeSql

class CondeSqlLocal(object):
    """Class for sql methods local."""
    csql = None

    def __init__(self):
        self.csql = CondeSql()

    def update_local_table_conde(self, list_insert, list_update):
        """Update table conde_info_local.

           Args:
             list_insert (list): list sql insert
             list_update (list): list sql update
           Returns:
             None
        """
        if len(list_insert) > 0:
            sql = "INSERT INTO conde_info_local "
            sql += "(name,version,path_local,path_onedrive,type,sha1,dt_created,dt_modified) "
            sql += "VALUES(?,?,?,?,?,?,?,?)"
            self.csql.execute_many(sql, list_insert)
        if len(list_update) > 0:
            sql = "UPDATE conde_info_local "
            sql += "SET name = ?,"
            sql += "path_local = ?,"
            sql += "path_onedrive = ?,"
            sql += "type = ?,"
            sql += "sha1 = ?,"
            sql += "dt_created = ?,"
            sql += "dt_modified = ?"
            sql += " WHERE version = ?"
            list_values_update = []
            for reg in list_update:
                name          = reg[0]
                version       = reg[1]
                path_local    = reg[2]
                path_onedrive = reg[3]
                type_r        = reg[4]
                id_onedrive   = reg[5]
                id_father_onedrive = reg[6]
                sha1        = reg[7]
                dt_created = reg[8]
                dt_modified = reg[9]

                list_values_update.append((name, path_local, path_onedrive, type_r, sha1, dt_created, dt_modified, version))
            self.csql.execute_many(sql, list_values_update)

    def update_ids_local(self, version, id_onedrive, id_father_onedrive):
        """Update id's onedrive in local table.

           Args:
             version (str): version
             id_onedrive (int): id onedrive
             id_father_onedrive (int): id father onedrive
           Returns:
             None
        """
        sql = "UPDATE conde_info_local "
        sql += " SET id_onedrive = '" + id_onedrive + "' , "
        sql += " id_father_onedrive = '" + id_father_onedrive + "' "
        sql += " WHERE version = " + version
        self.csql.execute_simple(sql)

    def update_version_sha1_onedrive(self, id_onedrive, id_father_onedrive, version, sha1):
        """Update version/sha1 onedrive in onedrive table.

           Args:
             version (str): version
             id_onedrive (int): id onedrive
             id_father_onedrive (int): id father onedrive
           Returns:
             None
        """
        sql = "UPDATE conde_info_onedrive "
        sql += " SET version = " + version
        sql += " , sha1 = '" + sha1 + "' "
        sql += " WHERE id_onedrive = '" + id_onedrive + "' "
        sql += " AND id_father_onedrive = '" + id_father_onedrive + "' "
        self.csql.execute_simple(sql)
