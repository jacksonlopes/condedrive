# -*- coding: utf-8 -*-
"""Sql methods onedrive.

__author__ = Jackson Lopes
__email__  = jacksonlopes@gmail.com
"""
from condesql import CondeSql

class CondeSqlRemote(object):
    """Class for sql methods onedrive."""
    csql = None

    def __init__(self):
        self.csql = CondeSql()

    def update_remote_table_conde(self, list_insert, list_update):
        """Update table conde_info_onedrive.

           Args:
             list_insert (list): list sql insert
             list_update (list): list sql update
           Returns:
             None
        """
        if len(list_insert) > 0:
            sql = "INSERT INTO conde_info_onedrive "
            sql += "(name,version,path_local,path_onedrive,type,id_onedrive,id_father_onedrive,sha1,dt_created,dt_modified) "
            sql += "VALUES(?,?,?,?,?,?,?,?,?,?)"
            self.csql.execute_many(sql, list_insert)
        if len(list_update) > 0:
            sql = "UPDATE conde_info_onedrive "
            sql += "SET version = ? ,name = ?,"
            sql += "path_local = ?,"
            sql += "path_onedrive = ?,"
            sql += "type = ?,"
            sql += "sha1 = ?,"
            sql += "dt_created = ?,"
            sql += "dt_modified = ?"
            sql += " WHERE id_onedrive = ? AND id_father_onedrive = ?"
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

                list_values_update.append((version, name, path_local, path_onedrive, type_r, sha1, dt_created, dt_modified, id_onedrive, id_father_onedrive))
                # update id_onedrive and id_father_onedrive in table conde_info_local
                # Atualiza id_onedrive e id_father_onedrive na tab. conde_info_local
                if version is None:
                    continue
                sql_loc = "UPDATE conde_info_local "
                sql_loc += " SET id_onedrive = '" + str(id_onedrive) + "' ,"
                sql_loc += " id_father_onedrive = '" + str(id_father_onedrive) + "' "
                sql_loc += " WHERE version = " + version
                self.csql.execute_simple(sql_loc)
            self.csql.execute_many(sql, list_values_update)

    def update_version_onedrive(self, version, id_onedrive, id_father_onedrive):
        """Update id's in onedrive table.

           Args:
             version (str): version
             id_onedrive (int): id onedrive
             id_father_onedrive (int): id father onedrive
           Returns:
             None
        """
        sql = "UPDATE conde_info_onedrive "
        sql += " SET version = " + version
        sql += " WHERE id_onedrive = '" + id_onedrive + "' AND "
        sql += " id_father_onedrive = '" + id_father_onedrive + "' "
        self.csql.execute_simple(sql)

    def update_versions_local_onedrive(self, new_version, old_version):
        """Update versions in local table.

           Args:
             new_version (str): new version
             old_version (str): old version
           Returns:
             None
        """
        sql = "UPDATE conde_info_local "
        sql += " SET version = " + new_version
        sql += " WHERE version = " + old_version
        self.csql.execute_simple(sql)
        sql = "UPDATE conde_info_onedrive "
        sql += " SET version = " + new_version
        sql += " WHERE version = " + old_version
        self.csql.execute_simple(sql)
