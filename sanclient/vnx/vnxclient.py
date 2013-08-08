'''
Created on Dec 13, 2012

@author: zhill
'''
from sanclient.sanclient import SANClient
import time
from sanclient.processtools import run_get_status
from sanclient.processtools import run_get_output
from sanclient.sanclient import SANConfig
from sanclient.sanclient import SANLun

#VNX Defaults
vnx_clone_complete_states = ['synchronized','consistent']
vnx_default_clone_id='0100000000000000'
vnx_default_storage_pool='0'
vnx_default_sp='a'
vnx_autoassign_true='1'
vnx_quiescethreshold='10'
vnx_default_migration_rate='high'
LUN_DELIMITER='LOGICAL UNIT NUMBER'

class VNXClient(SANClient):
    '''
    VNX implementation of the SANClient
    '''
    _my_config = None
    _cmd_base = ''

    def __init__(self, config):
        '''
        Constructor
        '''
        self._my_config = config
        
    def _parse_lun_list(self, output):
        '''Constructs a list of SANLun objects from the given input string'''
        luns = []
        single_lun_output = ''
        for line in output.splitlines():
            line = line.strip()
            if line.startswith(LUN_DELIMITER):                
                single_lun_output = line + '\n'
            elif line == "" or line == None:
                #separator, parse it now.
                luns.append(self._construct_lun(single_lun_output))
            else:
                single_lun_output += line + '\n'
        
        return luns
        
    def _construct_lun(self, output):
        '''Constructs a SANLun object from the string'''
        
        '''Example output from naviseccli lun -list -name <name>        
        LOGICAL UNIT NUMBER 1000
        Name:  zpythontestlun1
        UID:  60:06:01:60:98:B0:30:00:10:14:C6:C5:71:45:E2:11
        Current Owner:  SP A
        Default Owner:  SP A
        Allocation Owner:  SP A
        User Capacity (Blocks):  20971520
        User Capacity (GBs):  10.000
        Consumed Capacity (Blocks):  27316224
        Consumed Capacity (GBs):  13.025
        Pool Name:  Pool 0
        Raid Type:  r_10
        Offset:  0
        Auto-Assign Enabled:  DISABLED
        Auto-Trespass Enabled:  DISABLED
        Current State:  Ready
        Status:  OK(0x0)
        Is Faulted:  false
        Is Transitioning:  false
        Current Operation:  None
        Current Operation State:  N/A
        Current Operation Status:  N/A
        Current Operation Percent Completed:  0
        Is Pool LUN:  Yes
        Is Thin LUN:  No
        Is Private:  No
        Is Compressed:  No
        Tiering Policy:  Auto Tier
        Initial Tier:  Highest Available
        Tier Distribution:  
        Performance:  100.00%    
        '''
        
        lun = SANLun()
        
        for line in output.splitlines():
            line = line.strip()
            if line.startswith('LOGICAL UNIT NUMBER'):
                chunks = line.split(' ')
                if len(chunks) == 4:
                    lun.id = int( chunks[3].strip() )
                else:
                    print "Invalid line: " + line
            else:
                chunks = line.split(':')
                if len(chunks) > 1:
                    if chunks[0].strip() == 'Name':
                        lun.name = chunks[1].strip()
                    elif chunks[0] == 'User Capacity (GBs)':
                        lun.size = int( float( chunks[1].strip() ) )
        if lun.id != -1:
            return lun
        else:
            return None
    
    def _construct_base_command(self, cmd):
        if(self._cmd_base == ''):
            self._cmd_base = [self._my_config.get_cli_path(), '-User', self._my_config.get_username(), '-Password', self._my_config.get_password(), '-Address', self._my_config.get_management_endpoints()[0], '-Scope', '0']
        
        full_command = self._cmd_base + cmd
        return full_command
    
    def _parse_clone_state(self, output):
        '''Parses the clone status from the output of a clone list'''
        sync_percent='0'
        for line in output.splitlines():
            line = line.strip()
            if line.startswith('PercentSynced'):
                chunks = line.split(':')
                if len(chunks) == 2:
                    sync_percent = chunks[1].strip()
                    sync_percent.replace('%','')
            elif line.startswith('CloneState'):                
                chunks = line.split(':')
                if len(chunks) > 1:
                    return chunks[1].strip()
                else:
                    print "unknown line: " + line
    
        if sync_percent == '100':
            return 'Synchronized'
        
        return 'unknown'
    
    def _parse_migration_state(self, output):
        '''Parses the lun migration status from the output of a migrate -list'''

        if output.strip() == 'No current migrations exist':
            return 'none'
        
        for line in output.splitlines():
            line = line.strip()
            if line.startswith('PercentSynced'):
                chunks = line.split(':')
                if len(chunks) == 2:
                    sync_percent = chunks[1].strip()
                    sync_percent.replace('%','')
            elif line.startswith('CloneState'):                
                chunks = line.split(':')
                if len(chunks) > 1:
                    return chunks[1].strip()
                else:
                    print "unknown line: " + line
    
        if sync_percent == '100':
            return 'Synchronized'
        
        return 'unknown'
        
    def create_lun(self, lun_name=None, lun_size=None):
        ''' Creates lun and returns lun's ID'''        
        if lun_name == None or lun_size == None:
            raise ValueError("Name and size must be specified")
        
        command = self._construct_base_command(create_lun_command(lun_name=lun_name,capacity=lun_size))
        print command
        status = run_get_status(command)
        if status != 0:
            print "Error creating lun"
            return None
        
        get_command = self._construct_base_command(get_lun_by_name_command(lun_name=lun_name))
        lun_output = run_get_output(get_command)
        return self._construct_lun(lun_output)
    
    def get_all_luns(self):
        '''Gets list of all luns'''
        command = self._construct_base_command(get_all_luns_command())
        output = run_get_output(command)
        return self._parse_lun_list(output)
        
    def get_lun_by_id(self, lun_id=None):
        '''Gets lun by id lookup'''
        command = self._construct_base_command(get_lun_by_id_command(lun_id=lun_id))
        output = run_get_output(command)
        return self._construct_lun(output)
    
    def get_lun_by_name(self, lun_name=None):
        command = self._construct_base_command(get_lun_by_name_command(lun_name=lun_name))
        output = run_get_output(command)
        return self._construct_lun(output)    
        
    def delete_lun(self, lun=None):
        '''Delete the lun'''
        cmd = self._construct_base_command(delete_lun_by_id_command(lun_id=lun.id))
        print cmd
        status = run_get_status(cmd)
        return (status == 0)
    
    def delete_lun_by_name(self, lun_name=None):
        '''Delete the lun using a name ref'''
        cmd = self._construct_base_command(delete_lun_by_name_command(lun_name=lun_name))
        print cmd
        status = run_get_status(cmd)
        return (status == 0)
    
    def clone_lun(self, src_lun=None, dest_name=None):
        '''Copy the src lun using clone'''
        
        clone_group_name = src_lun.name + "-" + dest_name + "-cg"
        try:
            print "Creating destination lun for clone " + dest_name
            dest = self.create_lun(lun_name=dest_name, lun_size=src_lun.size) 

            try:
                for i in range(5):
                    print "Creating clone group " + clone_group_name
                    if self.create_clone_group(name=clone_group_name, src_lun=src_lun):
                        print 'Create clonegroup succeeded on the ' + str(i) + ' iteration with ' + str(i*3) + ' seconds of sleep'
                        break
                    else:
                        print "Retrying clone group creation, attempt " + str(i) + ' failed'
                        time.sleep(3)
                else:
                    print 'Failed after all retries in loop, aborting'
                    raise Exception('Could not create clone group')
                
                try:
                    print "Adding clone to clone group"
                    for i in range(5):                        
                        if self.add_lun_to_clone_group(cg_name=clone_group_name,lun=dest):
                            print 'Adding clone succeeded on the ' + str(i) + ' iteration with ' + str(i) + ' seconds of sleep'
                            break
                        else:
                            print "Retrying clone add, attempt " + str(i) + ' failed'
                            time.sleep(1)
                    else:
                        print 'Failed after all retries in loop, aborting'
                        raise Exception('Could not add clone to clone group')
                    
                    for i in range(3):
                        time.sleep(3)
                        cloneid = self.get_clone_id(cg_name=clone_group_name, lun=dest)
                        if cloneid == None:
                            print 'Could not get clone id of new clone lun'
                        else:
                            break;
                    else:
                        print 'Never got the clone id for the lun'
                        raise Exception('Could not get clone id')
                        
#Wait for completion
                    try:
                        while not self.clone_complete(group_name=clone_group_name, clone_id=vnx_default_clone_id):
                            print 'Sleeping for 5 sec'
                            time.sleep(5)
                    except Exception as wait_ex:
                        print "Failed waiting for clone to finish"
                    finally:
                        try:
                            print "Fracturing clone on cleanup"
                            self.fracture_clone(cg_name=clone_group_name) #Use the default clone id, change this if testing multiple concurrent clones
                        except:
                            print "Fracture failed"
                except Exception as clone_ex:
                    print "Failed adding clone: " + str(clone_ex)
                finally:
                    try:
                        self.remove_clone_from_group(cg_name=clone_group_name) #use the default cloneId
                    except:
                        print "Removing clone from group failed"
            except Exception as lun_ex:
                print "Failed in lun creation zone: " + str(lun_ex)
            
        except Exception as clone_dest_ex:
            print "Failed: " + str(clone_dest_ex)
            try:
                self.delete_lun_by_name(dest_name)
            except:
                print "Dest lun delete failed...this may be okay if it was never created"                
        finally:
            print "Deleting clone group"
            self.delete_clone_group(cg_name=clone_group_name)
            
        print "Clone complete"
        return dest
        
    def create_clone_group(self, name=None, src_lun=None):        
        '''Create a clone group'''
        if src_lun == None:
            return False
        
        cmd = self._construct_base_command(create_clone_group_command(cg_name=name,src_lun_id=src_lun.id))
        print cmd
        status = run_get_status(cmd)
        return (status == 0)
    
    def add_lun_to_clone_group(self,cg_name=None, lun=None):
        '''Adds a lun to a clonegroup as a clone, returns the clone id'''
        cmd = self._construct_base_command(add_lun_to_clone_group_command(group_name=cg_name, lun_id=lun.id))
        print cmd
        status = run_get_status(cmd)        
        return (status == 0)

    def get_clone_id(self, cg_name=None, lun=None):
        cmd = self._construct_base_command(get_clone_id_command(group_name=cg_name))
        print cmd
        output = run_get_output(cmd)
        clone_id = self._parse_clone_id_output(lun_id=lun.id, output=output)
        return clone_id
    
    def _parse_clone_id_output(self, lun_id=None, output=None):
        '''
        Parses the output from a "clone -listclone -cloneluns" command and returns the clone id
        of the requested lun.
        Example output to parse:

        Name:  test1
        CloneGroupUid:  50:06:01:60:BE:A0:58:4D:00:02:00:00:00:00:00:00

        CloneID:  0100000000000000
        CloneLUNs:  15

        CloneID:  0200000000000000
        CloneLUNs:  16

        example output if lun=15 would be 0100000000000000
        '''
        last_id = None
        for line in output.splitlines():
            line = line.strip()
            if line.startswith('CloneID:'):
                last_id = line.split(' ')[2].strip()
            elif line.startswith('CloneLUNs:') and line.split(' ')[2].strip() == str(lun_id):
                return last_id
        
    def clone_complete(self, cg_name=None, clone_id=vnx_default_clone_id):
        '''Check status of clone operation, true if done, false if still pending'''
        cmd = self._construct_base_command(get_clone_command(group_name=cg_name, clone_id=clone_id))
        print cmd
        output = run_get_output(cmd)
        status = self._parse_clone_state(output)
        
        if status != None:
            status = status.lower()

        return status in vnx_clone_complete_states  
    
    def fracture_clone(self, cg_name=None, clone_id=vnx_default_clone_id):
        cmd = self._construct_base_command(fracture_clone_command(group_name=cg_name,clone_id=clone_id))
        print cmd
        status = run_get_status(cmd)        
        return (status == True)
    
    def remove_clone_from_group(self, cg_name=None, clone_id=vnx_default_clone_id):
        cmd = self._construct_base_command(remove_clone_from_clonegroup_command(group_name=cg_name,clone_id=clone_id))
        print cmd
        status = run_get_status(cmd)
        return (status == True)

    def delete_clone_group(self, cg_name=None):
        cmd = self._construct_base_command(delete_clone_group_command(group_name=cg_name))
        print cmd
        status = run_get_status(cmd)
        return (status == 0)

    def clone_group_exists(self, cg_name=None):
        print 'Checking for clone group ' + cg_name
        cmd = self._construct_base_command(get_clone_group_command(group_name=cg_name))
        print cmd
        status = run_get_status(cmd)
        return (status == 0)        
    
    def snapshot_lun(self, lun_name=None):
        print 'Snapshot lun'
        
    def create_snapshot(self, src_lun=None, snap_name=None):
        cmd = self._construct_base_command(create_snapshot_command(name=snap_name,src_lun_id=src_lun.id))
        print cmd
        status = run_get_status(cmd)        
        return (status == 0)        
    
    def delete_snapshot(self, snap_name=None):
        cmd = self._construct_base_command(delete_snapshot_command(name=snap_name))
        print cmd
        status = run_get_status(cmd)        
        return (status == 0)        
        
    def create_mountpoint(self, src_lun=None, mount_name=None):
        cmd = self._construct_base_command(create_mountpoint_command(name=mount_name, src_lun_id=src_lun.id))
        print cmd
        status = run_get_status(cmd)
        if status != 0:
            return None
        
        result = self.get_lun_by_name(lun_name=mount_name)
        if result.id > 0:
            return result
    
    def attach_mountpoint(self, snap_name=None, mount_point=None):
        cmd = self._construct_base_command(attach_snapshot_mountpoint_command(mount_point_id=mount_point.id, snapshot=snap_name))
        print cmd
        status = run_get_status(cmd)

        return (status == 0)
    def detach_snap(self, snap_name=None, mount_point=None):
        cmd = self._construct_base_command(detach_snapshot_mountpoint_command(snapshot=snap_name))
        print cmd
        status = run_get_status(cmd)
        return (status == 0)
        
    def start_migrate_lun(self, src_lun=None, dest_lun=None):
        cmd = self._construct_base_command(start_lun_migration_command(src_lun_id=src_lun.id,dest_lun_id=dest_lun.id))
        print cmd
        status = run_get_status(cmd)
        return (status == 0)
    
    def migration_complete(self, migration_lun=None):
        cmd = self._construct_base_command(get_migration_state_command(src_lun_id=migration_lun.id))
        print cmd
        output = run_get_output(cmd)
        status = self._parse_migration_status(output)
        return status in ['none','complete']
    
    def _parse_migration_status(self,output=None):
        for line in output.splitlines():
            line = line.strip()
            if line.lower().startswith('current state'):
                return line.lower().split(':')[1]
        return 'none'
    
#END VNXClient class

def get_default_client(usr=None,password=None):
    '''Returns a default-configured VNXClient for the Eucalyptus QA system.'''
    return VNXClient(SANConfig(cli_path='/opt/Navisphere/bin/naviseccli',usrname=usr,passwd=password,manage_endpts=['192.168.25.180'],data_endpts=['192.168.25.182']))


#--------------------lun commands-------------------------
def create_lun_with_id_command(lun_name=None, lun_id=None, capacity=None, sp=None):
    return ['lun','-create', '-type','nonthin','-poolId', vnx_default_storage_pool, '-sp', vnx_default_sp,'-name',lun_name,'-l',str(lun_id),'-capacity',str(capacity),'-sq','gb']

def create_lun_command(lun_name=None, capacity=None):
    #Always uses SP A
    return ['lun','-create', '-type','nonthin','-poolId', vnx_default_storage_pool, '-sp',vnx_default_sp,'-name',lun_name,'-aa',vnx_autoassign_true,'-capacity',str(capacity),'-sq','gb']

def delete_lun_by_id_command(lun_id=None):
    return ['lun','-destroy','-l',str(lun_id), '-o']    

def delete_lun_by_name_command(lun_name=None):
    return ['lun','-destroy','-name', lun_name, '-o']
    
def expand_lun_command(lun_id=None, new_capacity=None):
    return ['lun','-expand', '-l',str(lun_id),'-capacity',str(new_capacity), '-sq','gb','-o']

def get_lun_by_id_command(lun_id=None):
    return ['lun','-list' , '-l',str(lun_id)]

def get_all_luns_command():
    return ['lun','-list']

def get_lun_by_name_command(lun_name=None):
    return ['lun','-list','-name',lun_name]

def get_lun_simple_command(lun_name=None):
    return ['lun','-list', '-name', lun_name, '-default']

def get_lun_properties_command(lun_name=None):
    return ['lun','-list','-name', lun_name, '-status', '-poolName','-userCap','-consumedCap','-state']

#--------------------storage group commands-------------------------
def create_storage_group_command(group_name=None):
    return ['storagegroup','-create','-gname', group_name]

def delete_storage_group_command(group_name=None):
    return ['storagegroup','-destroy', 'gname', group_name, '-o']

def add_lun_to_storage_group_command(group_name=None, lun_id=None, hlu=None):
    return ['storagegroup','-addhlu','-gname',group_name,'hlu',str(hlu), '-alu',str(lun_id)]

def remove_lun_from_storage_group_command(group_name=None, hlu=None):
    return ['storagegroup','-removehlu','-gname',group_name,'hlu',str(hlu), '-o']

def add_host_to_storage_group_command(group_name=None, host_iqn=None, sp=None, sp_port=None):
    return ['storagegroup','-setpath','-gname','-arraycommpath', '1', '-failovermode', '4', '-hbauid', host_iqn, '-sp', sp, '-spport', str(sp_port),'-unitserialnumber','array','-o']

def remove_host_from_storage_group_command(group_name=None, host_iqn=None):
    return ['storagegroup','-disconnecthost','-gname',group_name,'-host',host_iqn, '-o']

#--------------------chap commands-------------------------
def add_chap_user_command(host_iqn=None, user_name=None, password=None):
    return ['chap','-adduser','-definedFor','initiator','-initiatorName',host_iqn,'-userName', user_name, '-secret', password]

def remove_chap_user_command(host_iqn=None, user_name=None):
    return ['chap','-deleteuser','-definedFor','initiator','-initiatorName', host_iqn,'-userName', user_name]
                      
#--------------------clone commands-------------------------
def create_clone_group_command(cg_name=None, src_lun_id=None, quiesce_threshold=vnx_quiescethreshold):
    return ['clone','-createclonegroup','-name',cg_name,'-luns',str(src_lun_id), '-quiescethreshold',str(quiesce_threshold),'-o']

def delete_clone_group_command(group_name=None):
    return ['clone','-destroyclonegroup','-name',group_name, '-o']

def get_clone_group_command(group_name=None):
    return ['clone','-listclonegroup','-name',group_name]

def fracture_clone_command(group_name=None, clone_id=None):
    return ['clone','-fractureclone','-name',group_name,'-cloneID',str(clone_id), '-o']

def remove_clone_from_clonegroup_command(group_name=None, clone_id=None):
    return ['clone','-removeclone','-name',group_name,'-cloneID',str(clone_id),'-o']

def get_clone_command(group_name=None,clone_id=None):
    return ['clone','-listclone','-name', group_name, '-CloneId', clone_id]

def get_clone_id_command(group_name=None):
    return ['clone','-listclone','-name', group_name, '-cloneluns']

def add_lun_to_clone_group_command(group_name=None, lun_id=None, require_sync=True, sync_rate='High'):
    return ['clone','-addclone','-Name', group_name, '-Luns', str(lun_id), '-IsSyncRequired', str(int(require_sync)) ,'-SyncRate', sync_rate]    

#--------------------snapshot commands-------------------------
def get_snapshot_command(name=None):
    return ['snap','-list','-name', name]

def create_snapshot_command(name=None,src_lun_id=None):
    return ['snap','-create','-res',str(src_lun_id), '-restype','lun','-name', name, '-allowReadWrite','yes']

def delete_snapshot_command(name=None):
    return ['snap','-destroy','-id', name, '-o']

def create_mountpoint_command(name=None, src_lun_id=None):
    return ['lun','-create','-type', 'snap', '-primaryLun', str(src_lun_id), '-name', name, '-allowInBandSnapAttach','yes']

def delete_mountpoint_command(name=None):
    return ['lun','-destroy','-name', name, '-o']

def attach_snapshot_mountpoint_command(mount_point_id=None, snapshot=None):
    return ['snap','-attach','-id', str(snapshot),'-res',str(mount_point_id)]

def detach_snapshot_mountpoint_command(snapshot=None):
    return ['snap','-detach','-id', snapshot]

#--------------------migration commands-------------------------
def start_lun_migration_command(src_lun_id=None, dest_lun_id=None, rate=vnx_default_migration_rate):
    return ['migrate', '-start', '-source', str(src_lun_id), '-dest', str(dest_lun_id), '-rate', rate, '-o']

def get_migration_state_command(src_lun_id=None):
    return ['migrate','-list','-source',str(src_lun_id)]

def cancel_migration_state_command(src_lun_id=None):
    return ['migrate','-cancel','-source',str(src_lun_id), '-o']


if __name__ == '__main__':
    print "Nothing to run"
    pass
    
