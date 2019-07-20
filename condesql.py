# -*- coding: utf-8 -*-
"""Sql methods.

__author__ = Jackson Lopes
__email__  = jacksonlopes@gmail.com
__url__    = https://jslabs.cc
__src__    = https://github.com/jacksonlopes/condedrive
"""
import sqlite3
from condeconstants import CondeConstants

class CondeSql(object):
    """Class for sql methods."""

    conn = None

    def __init__(self):
        """If db not exists.. create.

           Args:
             None
           Returns:
             None
        """
        self.conn = sqlite3.connect(CondeConstants().NAME_DATABASE, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")

    def execute_simple(self, sql):
        """Insert/update/remove simple sql.

           Args:
             sql (str): SQL
           Returns:
             None
        """
        cursor = self.conn.cursor()
        cursor.execute(sql)
        self.conn.commit()

    def execute_simple_values(self, sql, values):
        """Insert/update/remove sql.

           Args:
             sql (str): SQL
             values (tuple): values
           Returns:
             None
        """
        cursor = self.conn.cursor()
        cursor.execute(sql, values)
        self.conn.commit()

    def execute_many(self, sql, list_data):
        """Insert/update/remove sql list.

           Args:
             sql (str): SQL
             list_data (tuple): list sql
           Returns:
             None
        """
        cursor = self.conn.cursor()
        cursor.executemany(sql, list_data)
        self.conn.commit()

    def execute_sql(self, sql, values):
        """Get result sql.

           Args:
             sql (str): SQL
             values (tuple): values
           Returns:
           (tuple) return sql
        """
        cursor = self.conn.cursor()
        if values != None:
            return cursor.execute(sql, values).fetchall()
        else:
            return cursor.execute(sql).fetchall()

    def insert_in_table(self, table, values):
        """Insert registry in table.

           Args:
             table (str): name of table
             values (tuple): values
           Returns:
             None
        """
        sql  = "INSERT INTO " + table
        sql += " (name,version,path_local,path_onedrive,type,id_onedrive,id_father_onedrive,sha1,dt_created,dt_modified) "
        sql += "VALUES(?,?,?,?,?,?,?,?,?,?)"
        self.execute_simple_values(sql, values)

    def normalize_tables(self):
        """Normalize tables.. sanitize news versions.

           Args:
             None
           Returns:
             None
        """
        # local
        sql = "SELECT t1.version FROM conde_info_local t1 "
        sql += "WHERE EXISTS (SELECT id_onedrive, id_father_onedrive FROM conde_info_local t2 "
        sql += "WHERE t2.id_onedrive = t1.id_onedrive AND t2.id_father_onedrive = t1.id_father_onedrive "
        sql += "GROUP BY id_onedrive, id_father_onedrive HAVING COUNT(*) > 1)"
        # reserve last registry
        # mantém último registro.
        list_local = self.execute_sql(sql, None)
        size = len(list_local) - 1
        for r in range(0, size):
            version = list_local[r][0]
            self.execute_simple("DELETE FROM conde_info_local WHERE version = " + version)
            self.execute_simple("DELETE FROM conde_info_onedrive WHERE version = " + version)

    def update_name_table(self, table, version, new_name):
        """Update name in table.

           Args:
             table (str): name of table
             version (str): version
             new_name (str): new name
           Returns:
             None
        """
        sql = "UPDATE " + table
        sql += " SET name = '" + new_name + "' "
        sql += " WHERE version = " + version
        self.execute_simple(sql)

    def normalize_paths_hierarchy(self, new_path_local, old_path_local, new_path_onedrive, old_path_onedrive):
        """Normalize paths when update hierarchy.

           Args:
             new_path_local (str): new path name
             old_path_local (str): old path name
             new_path_onedrive (str): new path onedrive
             old_path_onedrive (str): old path onedrive
           Returns:
             None
        """
        self.normalize_paths_hierarchy_exec("conde_info_local", new_path_local, old_path_local, new_path_onedrive, old_path_onedrive)
        self.normalize_paths_hierarchy_exec("conde_info_onedrive", new_path_local, old_path_local, new_path_onedrive, old_path_onedrive)

    def normalize_paths_hierarchy_exec(self, table, new_path_local, old_path_local, new_path_onedrive, old_path_onedrive):
        """Normalize paths when update hierarchy.

           Args:
             table (str): name of table
             new_path_local (str): new path name
             old_path_local (str): old path name
             new_path_onedrive (str): new path onedrive
             old_path_onedrive (str): old path onedrive
           Returns:
             None
        """
        sql = "SELECT * FROM " + table
        sql += " WHERE path_local like '" + old_path_local + "%' "
        sql += " AND path_onedrive like '" + old_path_onedrive + "%' "
        list_local = self.execute_sql(sql, None)
        list_update = []
        for rloc in list_local:
            version = rloc[2]
            if version is None:
                continue
            up_path_local = new_path_local + rloc[3][len(old_path_local):]
            up_path_onedrive = new_path_onedrive + rloc[4][len(old_path_onedrive):]
            list_update.append([up_path_local, up_path_onedrive, version])
        sql = "UPDATE " + table + " SET path_local = ? , path_onedrive = ? WHERE version = ?"
        self.execute_many(sql, list_update)
