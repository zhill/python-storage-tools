'''
Created on Dec 13, 2012

@author: zhill
'''

from sanclients import sanclient
from sanclients.vnx import vnxclient
from utils import processtools
import time
from threading import Thread
import argparse

lun_list=['src_lun_16gb','src_lun_32gb','src_lun_64gb','src_lun_128gb','src_lun_256gb']
global_config=None

def run_clone_suite(luns=None, iterations=4):
    '''
    Runs the clone test multiple times, set the iterations to determine how many tests to run
    '''
    if luns == None:
        print 'Must specify a lun list argument'
        return

    print 'Running clone benchmarks ' + str(iterations) + ' times'
    results = []
    for i in range(iterations):
        print 'Running iteration ' + str(i)
        results.append(run_clone_bench(luns=luns))
        print 'Result for clone iteration ' + i + ' = ' + str(results[i])

    print 'Full clone results = ' + str(results)
    return results

def run_migrate_suite(luns=None, iterations=4):
    '''
    Runs the migrate test multiple times, set the iterations to determine how many tests to run
    '''
    if luns == None:
        print 'Must specify a lun list argument'
        return

    print 'Running migrate benchmarks ' + str(iterations) + ' times'
    results = []
    for i in range(iterations):
        print 'Running iteration ' + str(i)
        results.append(run_migrate_bench())
        print 'Result for migrate iteration ' + i + ' = ' + str(results[i])

    print 'Full migrate results = ' + str(results)
    return results

def run_concurrent_migrate_bench(luns=None, concurrency=4):
    '''
    Runs a concurrent test by running the single migrate operation concurrently
    in individual threads. Uses a global variable to aggregate results
    '''
    if luns == None:
        print 'Must specify a lun list argument'
        return

    concurrent_results = {}
    current_thread = None
    print 'Running ' + str(concurrency) + ' migrate tests on ' + str(luns)
    for lun in luns:
        migrate_threads = []
        print 'Running concurrent tests'
        print 'Initializing result dictionary for ' + lun
        concurrent_results[lun] = []
        for i in range(concurrency):
            print 'Starting thread ' + str(i)
            dest_lun = lun + '-dest-' + str(i)
            current_thread = migrateThread(lun, dest_lun, concurrent_results)
            migrate_threads.append(current_thread)
            current_thread.start()
            time.sleep(1)

        while True:
            print 'Waiting on threads to terminate'
            time.sleep(5)
            for t in migrate_threads:
                print 'Checking thread ' + t.name
                if t.is_alive():
                    print 'Thread ' + t.name + ' still running'
                    break
                else:
                    print 'Thread ' + t.name + ' is finished'
            else:
                print 'No worker threads detected to be alive'
                break

        print 'Threads complete for src lun ' + lun + '. Results = ' + str(concurrent_results)

    return concurrent_results

def run_concurrent_clone_bench(luns=None, concurrency=4):
    '''
    Runs a concurrent test by running the single migrate operation concurrently
    in individual threads. Uses a global variable to aggregate results
    '''
    if luns == None:
        print 'Must specify a lun list argument'
        return

    concurrent_results = {}
    print 'Running ' + str(concurrency) + ' clone tests on list: ' + str(luns)
    current_thread = None
    for lun in luns:
        clone_threads = []
        print 'Running concurrent tests'
        print 'Initializing result dictionary for ' + lun
        concurrent_results[lun] = []
        for i in range(concurrency):
            print 'Starting thread ' + str(i)
            dest_lun = lun + '-dest-' + str(i)
            current_thread = cloneThread(lun, dest_lun, concurrent_results)
            clone_threads.append(current_thread)
            current_thread.start()
            time.sleep(1)

        while True:
            print 'Waiting on threads to terminate'
            time.sleep(5)
            for t in clone_threads:
                print 'Checking thread ' + t.name
                if t.is_alive():
                    print 'Thread ' + t.name + ' still running'
                    break
                else:
                    print 'Thread ' + t.name + ' is finished'
            else:
                print 'No worker threads detected to be alive'
                break

        print 'Threads complete for src lun ' + lun + '. Results = ' + str(concurrent_results)
    return concurrent_results

class migrateThread(Thread):
    def __init__(self, lun=None, dest_name=None, results_dict=None):
        Thread.__init__(self)
        self.src_lun=lun
        self.dest_lun_name=dest_name
        self.results = results_dict

    def run(self):
        '''
        Runs a single migration operation but wraps it such that this
        can be made an individual thread and places its results in the
        global dictionary.
        '''
        if self.results == None:
            print 'Must specify a results dictionary argument'
            return
        
        result = migrate_single_lun(src_lun_name=self.src_lun, dest_lun_name=self.dest_lun_name)
        self.results[self.src_lun].append(result)

class cloneThread(Thread):
    def __init__(self, lun=None, dest_name=None, results_dict=None):
        Thread.__init__(self)
        self.src_lun=lun
        self.dest_lun_name=dest_name
        self.results = results_dict

    def run(self):
        '''
        Runs a single clone operation but wraps it such that this
        can be made an individual thread and places its results in the
        global dictionary.
        '''
        if self.results == None:
            print 'Must specify a results dictionary argument'
            return

        result = clone_single_lun(src_lun_name=self.src_lun, dest_lun_name=self.dest_lun_name)
        self.results[self.src_lun].append(result)
        
def run_clone_bench(config=None, luns=None):
    if luns == None:
        print 'Must specify a lun list argument'
        return

    print 'Running cloning benchmarks'
    result_list=[]
    for lun in luns:
        print "Running clone test for " + lun
        total_time = clone_single_lun(sanconfig=config, src_lun_name=lun)
        print "Total time: " + str(total_time)
        result_list.append(total_time)
        time.sleep(30)

    print "Results: " + str(result_list)
    return result_list

def run_migrate_bench(config=None, luns=None):    
    if luns == None:
        print 'Must specify a lun list argument'
        return

    print 'Running migration benchmarks'
    result_list=[]
    for lun in luns:
        print "Running migrate test for " + lun
        total_time = migrate_single_lun(sanconfig=config, src_lun_name=lun)
        print "Total time: " + str(total_time)
        result_list.append(total_time)
        time.sleep(30)
    print "Results " + str(result_list)
    return result_list
    
def clone_single_lun(sanconfig=None, client=None, src_lun_name=None, dest_lun_name=None, cleanup_src=False):
    '''Returns the time (integer) to clone the lun, only measures the clone itself'''
    if src_lun_name == None:
        print 'No source lun given, cannot clone.'
        return
    
    print 'Cloning lun' + src_lun_name
    if client == None:
        if sanconfig == None:
            print 'No config provided. Cannot create client'
        else:        
                print 'Creating client using provide config'
                client = vnxclient.VNXClient(sanconfig)
    else:
        print 'Using extant client'
        
    print client
        
    src_lun = client.get_lun_by_name(src_lun_name)
        
    if src_lun == None:
        print 'Could not get source lun. Failing now'
        return
        
    if dest_lun_name == None:
        dest_name = src_lun.name + "-destination"
    else:
        dest_name = dest_lun_name

    total_time = 0
    start_time = None
    clone_group_name = src_lun.name + "-cg"

    try:
        print "Creating destination lun for clone " + dest_name
        dest = client.create_lun(lun_name=dest_name, lun_size=src_lun.size) 

        try:
            for i in range(5):
                print "Creating clone group " + clone_group_name
                try:
                    if client.create_clone_group(name=clone_group_name, src_lun=src_lun):
                        print 'Create clonegroup succeeded on the ' + str(i) + ' iteration with ' + str(i*3) + ' seconds of sleep'
                        break
                    else:
                        if client.clone_group_exists(cg_name=clone_group_name):
                            print 'Clone group ' + clone_group_name + ' already exists'
                            break

                        print "Retrying clone group creation, attempt " + str(i) + ' failed'
                        time.sleep(3)
                except:
                    if client.clone_group_exists(cg_name=clone_group_name):
                        print 'Clone group ' + clone_group_name + ' already exists'
                        break

            else:
                print 'Failed after all retries in loop, aborting'
                raise Exception('Could not create clone group')
            
            try:
                print "Adding clone to clone group"
                for i in range(5):
                    if client.add_lun_to_clone_group(cg_name=clone_group_name,lun=dest):
                        print 'Adding clone succeeded on the ' + str(i) + ' iteration with ' + str(i) + ' seconds of sleep'
                        start_time=time.time()
                        break
                    else:
                        print "Retrying clone add, attempt " + str(i) + ' failed'
                        time.sleep(1)
                else:
                    print 'Failed after all retries in loop, aborting'
                    raise Exception('Could not add clone to clone group')
                
                print "Getting clone id"
                clone_id = None
                for i in range(3):
                    clone_id = client.get_clone_id(cg_name=clone_group_name,lun=dest)
                    if clone_id != None:
                        print 'Getting clone id succeeded on the ' + str(i) + ' iteration with ' + str(i) + ' seconds of sleep'
                        print 'Clone id for ' + dest.name + ' is ' + clone_id
                        break
                    else:
                        print "Retrying clone id fetch, attempt " + str(i) + ' failed'
                        time.sleep(3)
                else:
                    print 'Failed after all retries in loop, aborting'
                    raise Exception('Could not determine clone id of added lun')
                                
                #Wait for completion
                try:
                    while not client.clone_complete(cg_name=clone_group_name, clone_id=clone_id):
                        print 'Sleeping for 5 sec'
                        time.sleep(5)
                except Exception as wait_ex:
                    print "Failed waiting for clone to finish" + str(wait_ex)
                finally:
                    total_time = time.time() - start_time
                    try:
                        print "Fracturing clone on cleanup"
                        client.fracture_clone(cg_name=clone_group_name, clone_id=clone_id) #Use the default clone id, change this if testing multiple concurrent clones
                    except:
                        print "Fracture failed"
            except Exception as clone_ex:
                print "Failed adding clone: " + str(clone_ex)
            finally:
                try:
                    client.remove_clone_from_group(cg_name=clone_group_name, clone_id=clone_id) #use the default cloneId
                except:
                    print "Removing clone from group failed"
        except Exception as lun_ex:
            print "Failed in lun creation zone: " + str(lun_ex)
        
    except Exception as clone_dest_ex:
        print "Failed: " + str(clone_dest_ex)
        try:
            client.delete_lun_by_name(dest_name)
        except:
            print "Dest lun delete failed...this may be okay if it was never created"                
    finally:
        print "Deleting clone group " + clone_group_name
        client.delete_clone_group(cg_name=clone_group_name)
            
    print "Clone complete"
    print 'Time: ' + str(total_time)
    
    if cleanup_src:
        print 'Doing lun cleanup of src'
        try:
            client.delete_lun_by_name(src_lun_name)
        except:
            print 'Failed to delete src lun'
    try:
        print 'Deleting destination lun: ' + dest_name
        client.delete_lun_by_name(dest_name)
    except:
        print 'Failed to delete dest lun'
    return total_time

def migrate_single_lun(sanconfig=None, client=None, src_lun_name=None, dest_lun_name=None, cleanup_src=False):
    print 'Migrating lun ' + src_lun_name

    if client == None:
        print 'Creating client instance'
        if sanconfig == None:
            print 'No config provided. Cannot create client'
        else:
            client = vnxclient.VNXClient(sanconfig)
    else:
        print 'Using extant client instance'
    
    if src_lun_name == None:
        src_name = 'migratesrc'
        print 'Creating a temporary lun for doing migration test: ' + src_name
        src_lun = client.get_lun_by_name(lun_name=src_name)        
        if src_lun == None:
            src_lun = client.create_lun(lun_name='migratesrc', lun_size=1)        
    else:
        src_name = src_lun_name
        src_lun = client.get_lun_by_name(lun_name=src_name)
        
    if src_lun == None or src_lun.id==-1:
        print "Could not get source lun. Failing now"
        return

    dest_name=None

    if dest_lun_name == None:
        dest_name = src_lun_name + '-migratedest'
    else:
        dest_name = dest_lun_name

    total_time = 0    
    start_time = None
    snap_name = src_lun.name + "-" + dest_name + "-snap"
    tmp_name = dest_name + '-templun'
    try:
        print 'Creating snapshot of src'
        if not client.create_snapshot(src_lun=src_lun,snap_name=snap_name):
            print 'Snapshot create failed'
            raise Exception('Could not create snapshot')
 
        print 'Creating mount point for src'
        #Mount point is a lun, but without size
        mount_point = client.create_mountpoint(src_lun=src_lun,mount_name=dest_name)
        
        print 'Creating temp destination lun' 
        tmp_lun = client.create_lun(lun_name=tmp_name, lun_size=src_lun.size)
        
        try:
            print 'Attaching snapshot to mount point'
            if not client.attach_mountpoint(snap_name=snap_name, mount_point=mount_point):
                print 'Failed snap attach'
                raise Exception('Failed snap attach')
            try:
                print 'Migrating mount point to full lun'
                start_time=time.time()
                if not client.start_migrate_lun(src_lun=mount_point,dest_lun=tmp_lun):                        
                    print 'Failed to initiate migration, aborting'
                    raise Exception('Could not initiate migration')
                
                #Wait for completion of migration
                try:
                    while not client.migration_complete(migration_lun=mount_point):
                        print 'Sleeping...'
                        time.sleep(5)
                    total_time = time.time() - start_time
                    print 'Migration complete!'                        
                except Exception as wait_ex:
                    print "Failed waiting for migration to finish" + str(wait_ex)
                    
            except Exception as migrate_ex:
                print 'Failed migrating lun: ' + str(migrate_ex)
                try:
                    client.cancel_migration(src_lun=mount_point)
                except:
                    print 'Migration cancellation failed'                                        
            finally:
                print 'Ensuring temp lun is gone'
                try:
                    tmp = client.get_lun_by_name(lun_name=tmp_lun.name)
                    if tmp == None:
                        raise Exception('Temp lun not found')
                    else:
                        print 'Error! Found tmp lun, deleting it. Should not find it if migration was done.'
                        try:
                            client.delete_lun(tmp)
                        except:
                            print 'Failed on temp lun deletion...could be ok'                        
                except:
                    print 'Tmp lun is gone. This is good'                
        except Exception as lun_ex:
            print "Failed snap attach: " + str(lun_ex)
        finally:
            print 'Detaching snapshot, this may fail and be ok'
            if not client.detach_snap(snap_name=snap_name, mount_point=mount_point):
                print 'Detach snap failed, this may be ok'
                
    except Exception as clone_dest_ex:
        print 'Failed: ' + str(clone_dest_ex)
        
    finally:
        try:
            client.delete_snapshot(snap_name=snap_name)
        except:
            print "Snap delete failed"
        
        try:
            print 'Deleting dest lun'
            client.delete_lun_by_name(dest_name)            
        except:
            print 'Dest lun delete failed...this may be okay if it was never created'
        
        try:
            if cleanup_src:
                print 'Deleting source lun since it was created for this test'
                client.delete_lun(src_lun)
        except:
            print 'Source lun cleanup failed'
            
    print 'Migration complete'
    print 'Time: ' + str(total_time)
    return total_time
    
#Global var to cache the local machine iqn
local_iqn = 'localiqn'

def get_iqn():
    '''Read iqn from /etc/iscsi/initiatorname.iscsi'''
    if local_iqn == 'localiqn':
        fd = open('/etc/iscsi/initiatorname.iscsi')
        name = fd.readline().split('=')[1].strip()
        print 'Found local iqn = ' + name
        local_iqn = name
        
    return local_iqn
    
#Unused so far    
def attach_lun_local(client=None, lun=None):
    print 'Attaching lun locally: ' + lun.name
    local_iqn = get_iqn()
    client.export_lun(lun=lun,host_iqn=local_iqn)
    
    host_attach(client=client, lun=lun)

#Unused so far
def host_attach(client=None, target_iqn=None):
    '''
    Attach the lun to the local host, assumes no CHAP authentication.
    Returns the name of the local device that is the attachment
    
    This is VNX specific for our setup, see the iqn and IP
    
    Also assumes only a single lun, so always looks for LUN 1 for device
    '''
    
    add_static_target = ['iscsiadm','-m','node','-T','iqn.1992-04.com.emc:cx.apm00121200804.a6', '-p','192.168.25.182', '-o', 'new']
    scan_sessions = ['iscsiadm','-m','session','-R']    
    iscsi_info = ['iscsiadm','-m','session','-P','3']
    
    processtools.run_get_status(add_static_target)
    processtools.run_get_status(scan_sessions)
    output = processtools.run_get_output(iscsi_info)
    
    parse_device_name(output,lun_id=1, target='iqn.1992-04.com.emc:cx.apm00121200804.a6')
    #TODO: finish this function
    local_device=None
    return local_device

#Unused so far
def parse_device_name(session_output=None, lun_id=None, target=None):
    current_target = ''
    current_lun = ''
    for line in session_output.splitlines():
        print 'Parsing line: ' + line
        line = line.strip()
        if line.startswith('Target').contains(target):
            #Parsing that section.
            current_target=line.split(':')[1]
        elif line.startswith('lun') and line.split(' ')[1] == str(lun_id):
            print 'found lun: ' + line
            current_lun = line.split('-')[1]
        elif line.contains('/dev/') and current_lun == str(lun_id) and current_target == target:
            print 'found dev' + line
            return line.split(' ')[1]
        
        #TODO: finish this function
    return ''            

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    #Use the default /opt/Navisphere/bin can change this later
    #parser.add_argument('-c','--clipath', action=help='path to naviseccli')
    parser.add_argument('-u','--user', required=True, help='username for SAN login')
    parser.add_argument('-p','--password', required=True, help='password for SAN login')
    parser.add_argument('-m','--management', nargs='+', required=True, help='management IP address/hostname for SAN login')
    parser.add_argument('-d','--data', nargs='+', required=True, help='data IP address/hostname for SAN login')
    args = parser.parse_args()
    
    config = sanclient.SANConfig(cli_path='/opt/Navisphere/bin/naviseccli',usrname=args.user,passwd=args.password,manage_endpts=args.management,data_endpts=args.data)
    print 'Starting benchmarks'
    run_clone_bench(config)
    run_migrate_bench(config)
    
    print 'Benchmarks complete'
    exit(0)
    
