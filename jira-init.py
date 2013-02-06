#!/usr/bin/python
#
# Init script for JIRA
#
# chkconfig: 123456 1 99
# description: JIRA init script
#
# Original Author: Josh Johnson
# Author: Sean McArdle
#
### BEGIN INIT INFO
# Provides: JIRA
# Required-Start: mysql
# Required-Stop: 
# Default-Start:  123456
# Default-Stop:  123456
# Short-Description: JIRA issue tracker
# Description: Web based project/issue tracking
### END INIT INFO

import sys, os, subprocess, re, time

APP_NAME = 'JIRA'
APP_DIR='/data/jira_main/jira-std/'
APP_START = 'bin/start-jira.sh'
APP_STOP = 'bin/stop-jira.sh'

def lock():
    """
    Create the /var/lock/subsys file
    """
    if not os.path.exists('/var/lock/subsys/'):
        os.makedirs('/var/lock/subsys/')

    open('/var/lock/subsys/' + APP_NAME, 'w').close()
    
def locked():
    """
    Return True if the lock file exists
    """
    return os.path.exists('/var/lock/subsys/' + APP_NAME)
    
def unlock():
    """
    Remove the /var/lock/subsys file
    """
    os.remove('/var/lock/subsys/' + APP_NAME)

def isAlive(pid):
    '''
    os.kill(pid, 0) does not kill the process and throws and exception if it
    doesn't exist.
    '''
    try:
        os.kill(int(pid), 0)
        return True
    except:            
        return False


def start():
    count = 0

    if not locked() and status() != 0:
        print('Starting ' + APP_NAME + '...')

        try:
            subprocess.check_call(APP_DIR + APP_START , shell=False)
        except:
            print('There was an error starting ' + APP_NAME)
            return subprocess.returncode

        lock()
        status()
    else:        
        print('Service locked, check status.')
        

def stop():
    """
    Shut everything down, clean up.
    """

    if locked():            
        print('Stopping ' + APP_NAME + '...')
        try:
            subprocess.check_call(APP_DIR + APP_STOP, shell=False)
            unlock()
        except:
            print('There was an error stopping ' + APP_NAME)
            return subprocess.returncode
        status()
    else:
        print('No process lock, check status.')
        

def restart():
    """
    Stop and then start
    """
    stop()    
    start()
    
def status():
    """
    Print any relevant status info, and return a status code, an integer:
    
    0	      program is running or service is OK
    1	      program is dead and /var/run pid file exists
    2	      program is dead and /var/lock lock file exists
    3	      program is not running
    4	      program or service status is unknown
    5-99	  reserved for future LSB use
    100-149	  reserved for distribution use
    150-199	  reserved for application use
    200-254	  reserved
    
    @see: http://dev.linux-foundation.org/betaspecs/booksets/LSB-Core-generic/LSB-Core-generic/iniscrptact.html
    """

    pidPath = APP_DIR + 'work/catalina.pid'

    if locked():
        if os.path.exists(pidPath):
            pid = open(pidPath, 'r').readline()
            if isAlive(pid):
                print('Processs running on pid: ' + str(pid))
                return 0
            else:
                print('Process not found, stale pid file exists.')
                unlock()
                return 1
        else:
            print('Can not find process although lock file exists.')
            return 2
    else:
        if os.path.exists(pidPath):
            pid = open(pidPath, 'r').readline()
            if isAlive(pid):
                lock()
                print('Processs running on pid: ' + str(pid))
                return 0
            else:
                print('Process not found, stale pid file exists.')
                return 1
        else:
            print(APP_NAME + ' is not running.')
            return 3
    
def test():
    """
    This is my way of "unit testing" the script. This function
    calls each of actions, mimicking the switchboard below. 
    
    It then verifies that the functions did what they were supposed to, 
    and reports any problems to stderr.
    
    @TODO: this could be used to inspect the system (e.g. open a web page if this is
    a web server control script) instead of the script.
    
    @TODO: you'll need to also check for PID files and running processes!
    """
    # Since this will turn off the system when its complete, 
    # I want to warn the user and give them the chance to opt out if they 
    # chose this option by accident.
    
    ok = raw_input("""
******************
TESTING MY SERVICE
******************

This will TURN OFF my-service after all the tests.

This should only be done for testing and debugging purposes.

Are you sure you want to do this? [Y/N]: """
    ).lower()
    
    if ok != 'y':
        print >> sys.stderr, "Aborting..."
        return
        
    print "Writing Lock File..."
    lock()
    print "Verifying lock file..."
    if os.path.exists('/var/lock/subsys/my-service'):
        print "Lock file written..."
    else:
        print >> sys.stderr, "ERROR: Lock file was NOT written"
    
    print "Starting..."
    start()
    # Do stuff to check the start() function     
    #
    # 
    
    # we call status a couple of times so we can test if it's returning the right
    # output under different circumstances
    status()
        
    print "Stopping..."
    stop()
    # Do stuff to check the stop() function     
    #
    # 
        
    print "Removing lock file..."
    unlock()
    
    if os.path.exists('/var/lock/subsys/my-service'):
        print >> sys.stderr, "ERROR: Could not remove lock file"
    else:
        print "Lock file removed successfully"
    
    # one more time to see what it looks like when the service off
    status()



# Main program switchboard - wrap everything in a try block to
# ensure the right return code is sent to the shell, and keep things tidy.
# 
# @TODO: need to raise custom exception instead of ValueError, and 
#        handle other exceptions better. 
#
# @TODO: put lock/unlock calls inside of start/stop?
if __name__ == '__main__':
    # if not root...kick out
    if not os.geteuid()==0:
        sys.exit("\nOnly root can run this script\n")

    try:
        # if there's fewer than 2 options on the command line 
        # (sys.argv[0] is the program name)
        if len(sys.argv) == 1:
            raise ValueError;  
            
        action = str(sys.argv[1]).strip().lower()
        
        if action == 'start':            
            start()
            sys.exit(0)
        elif action == 'stop':
            stop()            
            sys.exit(0)
        elif action == 'restart' or action == 'force-reload':
            restart()
            sys.exit(0)
        elif action == 'status':
            OK = status()
            sys.exit(OK)
        elif action == 'test':
            test()
            sys.exit(0)
        else:
            raise ValueError
    
    except (SystemExit):
        # calls to sys.exit() raise this error :(
        pass
    except (ValueError):
        print >> sys.stderr, "Usage: my-service [start|stop|restart|force-reload|status|test]"
        # return 2 for "bad command line option"
        sys.exit(2)
    except:
        # all other exceptions get caught here
        extype, value = sys.exc_info()[:2]
        print >> sys.stderr, "ERROR: %s (%s)" % (extype, value)
        # return 1 for "general error"
        sys.exit(1)
