# -*- coding: utf-8 -*-
"""Utils methods for program.

__author__ = Jackson Lopes
__email__  = jacksonlopes@gmail.com
"""
import os
import logging
import onedrivesdk
from onedrivesdk.version_bridge import fragment_upload
from condeconstants import CondeConstants

class CondeOnedriveUtils(object):
    """Class for utils methods."""
    client = None
    log    = logging.getLogger(CondeConstants().LOGGER_NAME)

    def __init__(self, client):
        self.client = client

    def enter_hierarchy_directory_onedrive(self, list_hierarchy_dir, source):
        """Enter hierarchy in onedrive.

           Args:
             list_hierarchy_dir (list): List hierarchy (FOTOS/familia/test)
             source(str): origin in onedrive
           Returns:
             (Item) Item representing the last directory
        """
        return self.create_hierarchy_directory_onedrive(list_hierarchy_dir, source)

    def create_hierarchy_directory_onedrive(self, list_hierarchy_dir, source):
        """Verify hierarchy in onedrive, create if required.

           Args:
             list_hierarchy_dir (list): List hierarchy (FOTOS/familia/test)
             source (str): origin in onedrive
           Returns:
             (Item) Item representing the last directory
        """
        # Return Item object conform last directory.
        # Allows you to navigate the structure
        # [Pictures,pessoal,sobrinhos]
        # Retorna o Item correspondente ao ultimo diretorio.
        # entao pode ser usado para navegar na estrutura.
        struct_hierarchy = list_hierarchy_dir.split('/')
        if struct_hierarchy[0] == "":
            return source

        for name_dir_create in struct_hierarchy:
            # check if exist name in source. Make if not exists.
            # Verifica se existe o nome na origem. Se nao tiver cria
            list_dir_onedrive = []
            list_dir, list_dir_onedrive = self.get_list_dir_onedrive(source)

            if name_dir_create not in list_dir_onedrive:
                source = self.create_dir_onedrive(name_dir_create, source)
            else:
                source = self.get_item_listitem_by_name(name_dir_create, list_dir)
        return source

    def get_list_dir_onedrive(self, item):
        """Return names directory by Item.

           Args:
             item (Item): Item representing onedrive
           Returns:
             (list) List dir and List names
        """
        list_dir = self.get_list_items(item)
        list_names = []
        for i in list_dir:
            if i.folder != None:
                list_names.append(i.name)
        return list_dir, list_names

    def get_list_items(self, item):
        """Return only itens directory current.

           Args:
             item (Item): Item representing onedrive
           Returns:
             (list) List itens
        """
        if not isinstance(item, str):
            item = item.id
        return self.client.item(id=item).children.get()

    def create_dir_onedrive(self, name_dir, item):
        """Create directory in onedrive.

           Args:
             name_dir (str): Name dir
             item (Item): Item representing in onedrive
           Returns:
             (list) List itens
        """
        if not isinstance(item, str):
            item = item.id
        folder = onedrivesdk.Folder()
        i = onedrivesdk.Item()
        i.name = name_dir
        i.folder = folder
        return self.client.item(id=item).children.add(i)

    def get_item_listitem_by_name(self, name_item, list_item):
        """Get list Item by name.

           Args:
             name_item (str): Name item
             list_item (list): List item
           Returns:
             (Item) Item onedrive
        """
        list_dir = list_item
        for i in list_dir:
            if i.folder != None and i.name == name_item:
                return i

    def get_item_by_name(self, name_item, item):
        """Get item (dir) onedrive by name.

           Args:
             name_item (str): Name item
             item (Item): Item representing in onedrive
           Returns:
             (Item) Item onedrive
        """
        list_dir = self.get_list_items(item)
        for i in list_dir:
            if i.folder != None and i.name == name_item:
                return i

    def get_item_file_by_name(self, name_item, item):
        """Get item (file) onedrive by name.

           Args:
             name_item (str): Name item
             item (Item): Item representing in onedrive
           Returns:
             (Item) Item onedrive
        """
        list_dir = self.get_list_items(item)
        for i in list_dir:
            if i.folder is None and i.name == name_item:
                return i

    def get_all_list_items(self, item):
        """Get all Item by source.

           Args:
             item (Item): Item representing in onedrive (source)
           Returns:
             (list) Item onedrive
        """
        if not isinstance(item, str):
            item = item.id
        list_item = self.client.item(id=item).delta(token=None).get()
        new_list_item = []
        while True:
            for i in list_item:
                new_list_item.append(i)
            try:
                list_item = onedrivesdk.ItemDeltaRequest.get_next_page_request(list_item, self.client, None).get()
            except AttributeError as e:
                break

        return new_list_item

    def get_hierarchy_dir_item(self, root, item):
        """Get hierarchy source -> root.

           Args:
             root (Item): Item representing in onedrive (root)
             item (Item): Item representing name in onedrive
           Returns:
             (list) List hierarchy
        """
        hierarchy = []
        hierarchy.append(item.name)
        while True:
            if item.id == root.id:
                break
            item = self.get_dir_root(item)
            item = self.get_item_by_id(item)
            hierarchy.append(item.name)
        return hierarchy[::-1] # reverse list | lista reversa

    def get_dir_root(self, item):
        """Get father Item.

           Args:
             item (Item): Item representing name in onedrive
           Returns:
             (str) id father
        """
        if not isinstance(item, str):
            item = item.id
        return self.client.item(id=item).get().parent_reference.id

    def get_item_by_id(self, item):
        """Get Item by id.

           Args:
             item (Item): Item representing in onedrive
           Returns:
             (Item) item
        """
        if not isinstance(item, str):
            item = item.id
        return self.client.item(id=item).get()

    def upload(self, name_file, path_local, id_remote, path_remote):
        """Upload file for Onedrive.

           Args:
             name_file (str): filename
             path_local (str): path local file
             id_remote (str): id Item onedrive
             path_remote (str): path remote (onedrive)
           Returns:
             (Item) item
        """
        if not isinstance(id_remote, str):
            id_remote = id_remote.id
        # Large file (> MAX_SINGLE_FILE_UPLOAD), fragment and upload..
        # Se arquivo for maior que MAX_SINGLE_FILE_UPLOAD, 100mb.. fragmenta e faz upload
        # senão faz pelo procedimento normal.
        if os.stat(path_local).st_size > CondeConstants().MAX_SINGLE_FILE_UPLOAD:
            self.client.item(drive="me", path=path_remote+'/'+name_file).upload_async(path_local, upload_status=self.info_upload)
            item = self.enter_hierarchy_directory_onedrive(path_remote, CondeConstants().DEFAULT_ONEDRIVE_DIR)
            return self.get_item_file_by_name(name_file, item)
        else:
            return self.client.item(drive="me", id=id_remote).children[name_file].upload(path_local)

    def info_upload(self, current_part, total_parts):
        """Show mb upload for large files.

           Args:
             current_part (int): current part size
             total_parts (int): total lenght file
           Returns:
             None
        """
        self.log.info("-- Sent " + str(current_part * 10) + "mb in " + str(total_parts * 10) + "mb")

    def download(self, item, path_local_save, filename):
        """Download file in Onedrive.

           Args:
             item (Item): Item in onedrive (directory)
             path_local_save (str): path local for save
             filename (str): filename
           Returns:
             True: OK
             False: Error
        """
        if not isinstance(item, str):
            item = item.id
        try:
            self.client.item(id=item).download(path_local_save + '/' + filename)
            return True
        except:
            os.remove(path_local_save + '/' + filename)
            return False

    def renamed_item(self, item, name):
        """Rename file in Onedrive.

           Args:
             item (Item): Item in onedrive (directory)
             name (str): new name
           Returns:
             (Item) Item onedrive
        """
        renamed_item = onedrivesdk.Item()
        renamed_item.name = name
        renamed_item.id = item.id
        return self.client.item(id=renamed_item.id).update(renamed_item)
