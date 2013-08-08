'''
Created on Dec 13, 2012

@author: zhill
'''
import os, sys, subprocess
import string
    
def run_get_status(cmd):
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        print e
        return e.returncode
    return 0

def run_get_output(cmd):
    p = subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    return p.communicate()[0]

if __name__ == '__main__':
    pass