#!/usr/local/bin/python2.7
# encoding: utf-8
'''
cleaners.vnxcleaner -- Cleans a VNX SAN of unwanted LUNs and Groups based on regex


It defines classes_and_methods

@author:     zhill
        
@copyright:  2013 Zach Hill
        
@license:    GGPL3

@contact:    zach@eucalyptus.com
@deffield    08-08-2013
'''

import sys
import os
import re

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
from sanclient.vnx.vnxclient import VNXClient
from sanclient.sanclient import SANConfig

__all__ = []
__version__ = 0.1
__date__ = '2013-08-08'
__updated__ = '2013-08-08'

DEBUG = 1
TESTRUN = 0
PROFILE = 0

# Is this a dry-run?
DRYRUN = False

def cleanLUNs(client=None, includeRegex=None, excludeRegex=None):
    '''Cleans LUNs from the specified SAN'''
    print 'Deleting LUNs that match ' + str(includeRegex) + ' but excluding matches for ' + str(excludeRegex)
    
    if client == None:
        raise(Exception('No client received.'))
    
    if includeRegex == '':
        includeRegex = None
        
    if excludeRegex == '': 
        excludeRegex = None
    
    print 'Getting luns'
    luns = []
    try:
        luns = client.get_all_luns()
    except Exception as e:
        print('Failed to get lun list',e)
        return 1
    
    for lun in luns:
        if (includeRegex == None or re.match(includeRegex, lun.name)) and (excludeRegex == None or not re.match(excludeRegex, lun.name)):
            if DRYRUN == True:
                print 'DRY RUN. Would delete: ' + lun.to_string()
            else:
                print 'Deleting LUN: ' + lun.to_string()
                try:
                    client.delete_lun()
                except Exception as e:
                    print('Error deleting lun:',e)            
                
        else:
            print 'Skipping LUN: ' + lun.to_string()
    
    print 'Cleaning complete!'
    return 0

class CLIError(Exception):
    '''Generic exception to raise and log different fatal errors.'''
    def __init__(self, msg):
        super(CLIError).__init__(type(self))
        self.msg = "E: %s" % msg
    def __str__(self):
        return self.msg
    def __unicode__(self):
        return self.msg

def main(argv=None): # IGNORE:C0111
    '''Command line options.'''
    global DRYRUN
    
    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = os.path.basename(sys.argv[0])
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
    program_shortdesc = __import__('__main__').__doc__.split("\n")[1]
    program_license = '''%s

  Created by zhill on August 8, 2013
  Copyright 2013 Eucalyptus Systems Inc. All rights reserved.
  
  Licensed under the GNU General Public License v3.0
  
  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
''' % (program_shortdesc)

    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
        #parser.add_argument("-r", "--recursive", dest="recurse", action="store_true", help="recurse into subfolders [default: %(default)s]")
        parser.add_argument("-v", "--verbose", dest="verbose", action="count", help="set verbosity level [default: %(default)s]")
        parser.add_argument("-i", "--include", dest="include", help="only include paths matching this regex pattern. Note: exclude is given preference over include. [default: %(default)s]", metavar="RE" )
        parser.add_argument("-e", "--exclude", dest="exclude", help="exclude paths matching this regex pattern. [default: %(default)s]", metavar="RE" )
        parser.add_argument('-V', '--version', action='version', version=program_version_message)
        parser.add_argument('-d', '--dryrun', action='store_true', help='Do a dry run, outputting what would happen, but not actual changing resources')
        parser.add_argument('-c', '--clipath', help='path to vnx naviseccli tool', default='/opt/Navisphere/bin/naviseccli')
        parser.add_argument('-u', '--user', required=True, help='username for SAN login')
        parser.add_argument('-p', '--password', required=True, help='password for SAN login')
        parser.add_argument('-m', '--management', nargs='+', required=True, help='management IP address/hostname for SAN login')
        
        # Process arguments
        args = parser.parse_args()

        #recurse = args.recurse
        recurse = False        
        verbose = args.verbose
        inpat = args.include
        expat = args.exclude
        DRYRUN = args.dryrun
        
        if verbose > 0:
            print("Verbose mode on")
            if recurse:
                print("Recursive mode on")
            else:
                print("Recursive mode off")

        if DRYRUN:
            print('Doing dry run. No resources will be changed')
        
        if inpat and expat and inpat == expat:
            raise CLIError("include and exclude pattern are equal! Nothing will be processed.")
                            
        config = SANConfig(cli_path=args.clipath,usrname=args.user,passwd=args.password,manage_endpts=args.management,data_endpts=[])
        client = VNXClient(config)
        cleanLUNs(client, inpat, expat)
        
        return 0
    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0
    except Exception, e:
        if DEBUG or TESTRUN:
            raise(e)
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        return 2

if __name__ == "__main__":
    if DEBUG:
        #sys.argv.append("-h")
        sys.argv.append("-v")
    if TESTRUN:
        import doctest
        doctest.testmod()
    if PROFILE:
        import cProfile
        import pstats
        profile_filename = 'cleaners.vnxcleaner_profile.txt'
        cProfile.run('main()', profile_filename)
        statsfile = open("profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
        
    sys.exit(main())
