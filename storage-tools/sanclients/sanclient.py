'''
Created on Dec 13, 2012

@author: zhill
'''

class SANClient:
    '''
    Top-level interface for SANClient implementations
    '''

    def __init__(self,params):
        '''
        Constructor
        '''
    
    def create_lun(self, lun_name=None, lun_size=None):
        ''' Creates lun and returns lun's ID'''        
    
    def delete_lun(self, lun=None):
        '''Delete the lun'''
    
    def get_lun_by_name(self, lun_name=None):
        '''Fetch lun id (int)'''
    
    def get_lun_by_id(self, lun_id=None):
         '''Fetch name of lun'''
    
    def clone_lun(self, lun_name=None):
        '''Clone the lun for some definition of "clone"'''
        
    def snapshot_lun(self, lun_name=None):
        '''Snapshot the lun for some definition of "snapshot"'''
    
    def delete_snapshot(self, snap_name=None):
        '''Delete the named snapshot (may or may not be a lun depending on implementation'''
    
    def delete_clone(self, clone_name=None):
        '''Delete the named clone (may or may not be a lun depending on implementation'''
        
    
class SANLun:
    '''
    Represents a lun on the SAN in a very simple form
    '''
    id=-1
    name=''
    size=-1
    
    def to_string(self):
        return 'LUN(' + str(self.id) + ', ' + str(self.name) + ', ' + str(self.size) + ')'
            
class SANGroup:
    '''
    Represents a group of luns and hosts. EMC StorageGroup or Netapp iGroup are examples, but this is generic
    '''
    id=''
    name=''
    hosts=[]
    luns=[]
    
    def to_string(self):
        return 'SAN Group(' + str(self.id) + ',' + str(self.name) + ' hosts= ' + str(self.hosts) + ' luns= ' + str(self.luns)
    
class SANConfig:
    '''
    Top-level interface for SAN configs
    '''
    _management_endpoints = []
    _data_endpoints = []
    _cli_path = None
    _username = None
    _password = None
    
    def __init__(self, cli_path, manage_endpts, data_endpts, usrname, passwd):
        self._management_endpoints = manage_endpts
        self._data_endpoints = data_endpts
        self._cli_path = cli_path
        self._username = usrname
        self._password = passwd
    
    def set_management_endpoints(self, endpts=None):
        self._management_endpoints = endpts
    
    def set_data_endpoints(self, endpts=None):
        self._data_endpoints = endpts

    def get_management_endpoints(self):
        return self._management_endpoints;
    
    def get_data_endpoints(self):
        return self._data_endpoints;
    
    def get_cli_path(self):
        return self._cli_path;

    def get_username(self):
        return self._username
    
    def get_password(self):
        return self._password
    
    