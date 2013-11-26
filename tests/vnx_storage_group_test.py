'''
Created on Nov 26, 2013

@author: zhill
'''
import unittest

from sanclients import sanclient
from sanclients.vnx import vnxclient
import argparse

#class Test(unittest.TestCase):
class StorageGroupTest:
    
    def testGroupParse(self, sanconfig=None):
        print 'Testing group parseing'        
        client = vnxclient.VNXClient(sanconfig)
        groups = client.get_all_storage_groups()
        print 'Got groups'
        for g in groups:
            print 'Group: ' + g.to_string()
        
    def testGroupListParse(self):
        '''
        Test group list parsing
        '''
        
        print 'Testing group list parsing'
        pass
        
    def testGroupCreate(self):
        '''
        Test storage group creation
        '''
        print 'Testing storage group creation'
        pass
    
    def testGroupDelete(self):
        '''
        Test storage group deletion
        '''
        print 'Testing storage group deletion'
        pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    
    parser = argparse.ArgumentParser()
    #Use the default /opt/Navisphere/bin can change this later
    #parser.add_argument('-c','--clipath', action=help='path to naviseccli')
    parser.add_argument('-u','--user', required=True, help='username for SAN login')
    parser.add_argument('-p','--password', required=True, help='password for SAN login')
    parser.add_argument('-m','--management', nargs='+', required=True, help='management IP address/hostname for SAN login')
    parser.add_argument('-d','--data', nargs='+', required=True, help='data IP address/hostname for SAN login')
    args = parser.parse_args()
    
    config = sanclient.SANConfig(cli_path='/opt/Navisphere/bin/naviseccli',usrname=args.user,passwd=args.password,manage_endpts=args.management,data_endpts=args.data)
    print 'Starting vnx storage group tests'
    
    #unittest.main()
    t = StorageGroupTest()
    t.testGroupParse(sanconfig=config)
    
    print 'Tests complete'