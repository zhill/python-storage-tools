"""
Created on Nov 26, 2013

@author: zhill
"""
import unittest

from sanclients import sanclient
from sanclients.vnx import vnxclient
import argparse

#class Test(unittest.TestCase):
class StorageGroupTest:
    
    def testGroupParse(self, sanconfig=None):
        print 'Testing single group parsing'
        client = vnxclient.VNXClient(sanconfig)
        group = client.get_group('iqn1998-01comvmware:g-12-05-0c0968d1')
        print 'Got group: ' + group.to_string()
        
    def testGroupListParse(self, sanconfig=None):
        """
        Test group list parsing
        """
        
        print 'Testing group list parsing'
        client = vnxclient.VNXClient(sanconfig)
        groups = client.get_all_groups()
        print 'Got groups'
        for g in groups:
            print 'Group: ' + g.to_string()
        
    def testGroupCreate(self, sanconfig=None):
        """
        Test storage group creation
        """
        print 'Testing storage group creation'
        pass
    
    def testGroupDelete(self, sanconfig=None):
        """
        Test storage group deletion
        """
        print 'Testing storage group deletion'
        
        client = vnxclient.VNXClient(sanconfig)
        group_name='iqn1994-05comredhat:5bf3a10e597'
        group = client.get_group(group_name)
        print 'Got group: ' + group.to_string()
        
        print 'Deleting group'
        client.delete_group(group_name)
        
        print 'Getting deleted group, should fail'
        group2 = client.get_group(group_name)
        print 'Got ' + group2.to_string()


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
    #t.testGroupParse(sanconfig=config)
    t.testGroupListParse(sanconfig=config)
    #t.testGroupDelete(sanconfig=config)
    
    print 'Tests complete'