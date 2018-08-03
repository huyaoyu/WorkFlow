
from __future__ import print_function

import os
import logging

class WFException(Exception):
    def __init__(self, message, name = None):
        self.message = message
        self.name = name

    def describe(self):
        if ( self.name is not None ):
            desc = self.name + ": " + self.message
        else:
            desc = self.message
    
        return desc

class AccumulatedValue(object):
    def __init__(self, name, plotFlag = True):
        self.name = name
        self.plotEnabled = plotFlag

        self.acc   = []
        self.stamp = []

        self.xLabel = "Stamp"
        self.yLabel = "Value"

    def push_back(self, v, stamp = None):
        self.acc.append(v)

        if ( stamp is not None ):
            self.stamp.append(stamp)
        else:
            if ( 0 == len(self.stamp) ):
                self.stamp.append(0)
            else:
                self.stamp.append( self.stamp[-1] + 1 )
    
    def push_back_array(self, a, stamp = None):
        nA = len(a)
        nS = 0

        if ( stamp is not None ):
            nS = len(stamp)
        
        if ( nA != nS ):
            # This is an error.
            desc = """Lengh of values should be the same with the length of the stamps.
            len(a) = %d, len(stamp) = %d.""" % (nA, nS)
            exp = WFException(desc, "push_back_array")
            raise(exp)

        for item in a:
            self.acc.append(item)

        flagEmpty = 0 == len(self.stamp)

        if ( stamp is not None ):
            for item in stamp:
                self.stamp.append(item)
        else:
            for i in range(nA):
                if ( flagEmpty ):
                    self.stamp.append(0)
                    flagEmpty = False
                else:
                    self.stamp.append( self.stamp[-1] + 1 )
    
    def clear(self):
        self.acc   = []
        self.stamp = []

    def last(self):
        if ( 0 == len(self.acc) ):
            # This is an error.
            desc = "The length of the current accumulated values is zero."
            exp = WFException(desc, "last")
            raise(exp)

        return self.acc[-1]

    def get_values(self):
        return self.acc

    def get_stamps(self):
        return self.stamp

    def show_raw_data(self):
        if ( True == self.plotEnabled ):
            plotEnabledString = "True"
        else:
            plotEnabledString = "False"
        
        print("%s with plotEnabled = %s" % (self.name, plotEnabledString))
        print("acc: ")
        print(self.acc)
        print("stamp: ")
        print(self.stamp)

class WorkFlow(object):
    def __init__(self, workingDir, logFilename = None):
        self.workingDir = workingDir # The working directory.

        if ( not os.path.isdir(self.workingDir) ):
            os.makedirs( self.workingDir )

        self.isInitialized = False
        self.AV = {"loss": AccumulatedValue("loss")}

        self.verbose = False

        if ( logFilename is not None ):
            self.logFilename = logFilename
        else:
            self.logFilename = "wf.log"
        
        # Logger.
        # logging.basicConfig(datefmt = '%m/%d/%Y %I:%M:%S')
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        streamHandler = logging.StreamHandler()
        streamHandler.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(levelname)s: %(message)s')
        streamHandler.setFormatter(formatter)

        self.logger.addHandler(streamHandler)

        logFilePathPlusName = self.workingDir + "/" + self.logFilename
        fileHandler = logging.FileHandler(filename = logFilePathPlusName, mode = "w")
        fileHandler.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
        fileHandler.setFormatter(formatter)

        self.logger.addHandler(fileHandler)

        self.logger.info("WorkFlow created.")

    def add_accumulated_value(self, name):
        # Check if there is alread an ojbect which has the same name.
        if ( name in self.AV.keys() ):
            # This is an error.
            desc = "There is already an object registered as \"%s\"." % (name)
            exp = WFException(desc, "add_accumulated_value")
            raise(exp)
        
        # Name is new. Create a new AccumulatedValue object.
        self.AV[name] = AccumulatedValue(name)

    def have_accumulated_value(self, name):
        return ( name in self.AV.keys() )

    def push_to_av(self, name, value, stamp = None):
        # Check if the name exists.
        if ( False == (name in self.AV.keys()) ):
            # This is an error.
            desc = "No object is registered as %s." % (name)
            exp = WFException(desc, "push_to_av")
            raise(exp)
        
        # Retrieve the AccumulatedValue object.
        av = self.AV[name]

        av.push_back(value, stamp)

    def initialize(self):
        # Check whether the working directory exists.
        if ( False == os.path.isdir(self.workingDir) ):
            # Directory does not exist, create the directory.
            os.mkdir(self.workingDir)
        
        if ( True == self.isInitialized ):
            # This should be an error.
            desc = "The work flow is already initialized."
            exp = WFException(desc, "initialize")
            raise(exp)

        self.isInitialized = True

        self.debug_print("initialize() get called.")

    def train(self):
        if ( False == self.isInitialized ):
            # This should be an error.
            desc = "The work flow is not initialized yet."
            exp = WFException(desc, "tain")
            raise(exp)
        
        self.debug_print("train() get called.")

    def test(self):
        if ( False == self.isInitialized ):
            # This should be an error.
            desc = "The work flow is not initialized yet."
            exp = WFException(desc, "test")
            raise(exp)

        self.debug_print("test() get called.")

    def finalize(self):
        if ( False == self.isInitialized ):
            # This should be an error.
            desc = "The work flow is not initialized yet."
            exp = WFException(desc, "finalize")
            raise(exp)
        
        self.isInitialized = False

        self.debug_print("finalize() get called.")

    def is_initialized(self):
        return self.isInitialized

    def debug_print(self, msg):
        if ( True == self.verbose ):
            print(msg)
