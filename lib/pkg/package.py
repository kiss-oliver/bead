from abc import ABCMeta, abstractmethod
from ..tech.timestamp import time_from_timestamp


class Package(object):
    '''
    I am providing high-level access to a content of a data package.
    '''

    __metaclass__ = ABCMeta

    uuid = str
    version = str
    timestamp_str = str

    @property
    def timestamp(self):
        return time_from_timestamp(self.timestamp_str)

    @abstractmethod
    def export(self, exported_archive_path):
        '''
        I pack my content (everything!) as a zip-Archive to requested location.
        '''
        pass

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
