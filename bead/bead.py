from abc import ABCMeta, abstractmethod
from .tech.timestamp import time_from_timestamp


class Bead(object):
    '''
    I am providing high-level access to content of a bead.
    '''

    __metaclass__ = ABCMeta

    bead_uuid = str
    hash_function_uuid = str
    content_hash = str
    timestamp_str = str
    box_name = str
    name = str

    @property
    def timestamp(self):
        return time_from_timestamp(self.timestamp_str)

    def unpack_to(self, workspace):
        self.unpack_code_to(workspace.directory)
        workspace.create_directories()
        self.unpack_meta_to(workspace)

    @abstractmethod
    def unpack_data_to(self, path):
        pass

    @abstractmethod
    def unpack_code_to(self, path):
        pass

    @abstractmethod
    def unpack_meta_to(self, workspace):
        pass
