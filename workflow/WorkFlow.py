
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
import threading
import time

# Visdom.
from visdom import Visdom

# Dash.
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from flask import request
from flask.logging import default_handler

# ============= Dash. ===========================

DASH_APP = dash.Dash()
DASH_APP.server.logger.removeHandler(default_handler)

# Handle the default logger of dash (flask)
flaskLogger = logging.getLogger( "werkzeug" )

flaskFileHandler = logging.FileHandler(filename = "./FlaskLog.log", mode = "w")
flaskFileHandler.setLevel(logging.DEBUG)

flaskLogger.handlers = []
flaskLogger.addHandler( flaskFileHandler )

sys.stderr = open('./HttpLog.log', 'w')

# Shutdown method. Copied from:
# https://stackoverflow.com/questions/15562446/how-to-stop-flask-application-without-using-ctrl-c
def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@DASH_APP.server.route('/shutdown', methods=['POST'])
def shutdown():
    shutdown_server()
    return 'Server shutting down...'

DASH_APP.layout = html.Div([
    dcc.Input(id='my-id', value='initial value', type='text'),
    html.Div(id='my-div', children="Children.")
])

@DASH_APP.callback(
    Output(component_id='my-div', component_property='children'),
    [Input(component_id='my-id', component_property='value')]
)
def update_output_div(input_value):
	
	print(input_value)

	if ( "q" == input_value[-1] ):
		print("quit")
		shutdown()
		return

	ret = "You\'ve entered {}".format(input_value)
	return ret

class DashThread(threading.Thread):
    """docstring for DashThread"""
    def __init__(self, name, app):
        super(DashThread, self).__init__()
        self.name = name
        self.app = app
	
    def run(self):
        self.app.run_server()
        print("%s: Dass app ends." % (self.name))

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
    def __init__(self, name, avgWidth = 2):
        self.name = name

        self.acc   = []
        self.stamp = []

        if ( avgWidth <= 0 ):
            exp = WFException("Averaging width must be a positive integer.", "AccumulatedValue")
            raise(exp)

        self.avg      = []
        self.avgWidth = avgWidth
        self.avgCount = 0

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
        
        # Calculate the average.
        if ( 0 == len( self.avg ) ):
            self.avg.append(v)
            self.avgCount = 1
        else:
            if ( self.avgCount < self.avgWidth ):
                self.avg.append(\
                    ( self.avg[-1] * self.avgCount + self.acc[-1] ) / ( self.avgCount + 1 ) )
                self.avgCount  += 1
            else:
                self.avg.append(\
                    ( self.avg[-1] * self.avgCount - self.acc[ -1 - self.avgCount ] + self.acc[-1] ) / self.avgCount \
                )
    
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

            for i in range(nA):
                self.push_back( a[i], stamp[i] )
        else:
            for i in range(nA):
                self.push_back( a[i] )
    
    def clear(self):
        self.acc   = []
        self.stamp = []
        self.avg   = []

    def last(self):
        if ( 0 == len(self.acc) ):
            # This is an error.
            desc = "The length of the current accumulated values is zero."
            exp = WFException(desc, "last")
            raise(exp)

        return self.acc[-1]

    def get_num_values(self):
        return len( self.acc )

    def get_values(self):
        return self.acc

    def get_stamps(self):
        return self.stamp

    def get_avg(self):
        return self.avg

    def show_raw_data(self):
        print("%s" % (self.name))
        print("acc: ")
        print(self.acc)
        print("stamp: ")
        print(self.stamp)

    def dump(self, outDir, prefix = "", suffix = ""):
        # Convert acc and avg into NumPy arrays.
        acc = np.column_stack( ( np.array(self.stamp).astype(np.float), np.array(self.acc).astype(np.float) ) )
        avg = np.column_stack( ( np.array(self.stamp).astype(np.float), np.array(self.avg).astype(np.float) ) )

        # Dump the files.
        np.save(    outDir + "/" + prefix + self.name + suffix + ".npy", acc )
        np.savetxt( outDir + "/" + prefix + self.name + suffix + ".txt", acc )

        np.save(    outDir + "/" + prefix + self.name + suffix + "_avg.npy", avg )
        np.savetxt( outDir + "/" + prefix + self.name + suffix + "_avg.txt", avg )

class AccumulatedValuePlotter(object):
    def __init__(self, name, av, avNameList, avAvgFlagList = None):
        self.name       = name
        self.AV         = av
        self.avNameList = avNameList

        if ( 0 == len( self.avNameList ) ):
            exp = WFException("The avNameList is empty.", "AccumulatedValuePlotter")
            raise(exp)

        # Pack the avNameList in to index dictionary.
        initIndexList = [-1] * len( self.avNameList )

        self.plotIndexDict = dict( zip(self.avNameList, initIndexList) )

        if ( avAvgFlagList is None ):
            avAvgFlagList = [False] * len( self.avNameList )
        else:
            if ( len(self.avNameList) != len(avAvgFlagList) ):
                exp = WFException("The lenght of avAvgFlagList should be the same with avNameList", "AccumulatedValuePlotter")
                raise(exp)
        
        self.avAvgFlagDict = dict( zip(self.avNameList, avAvgFlagList) )

        self.title = self.name
        self.xlabel = "xlabel"
        self.ylabel = "ylabel"
    
    def initialize(self):
        # The method of the base class cannot be invoked.
        exp = WFException("initialize() of AccumulatedValuedPlotter base class could no be invoked directly.", "AccumulatedValuePlotter")
        raise(exp)

    def update(self):
        # The method of the base class cannot be invoked.
        exp = WFException("update() of AccumulatedValuedPlotter base class could no be invoked directly.", "AccumulatedValuePlotter")
        raise(exp)
    
    def write_image(self, outDir, prefix = "", suffix = ""):
        fig, ax = plt.subplots( nrows=1, ncols=1 )
        legend = []

        for name in self.avNameList:
            av = self.AV[name]

            ax.plot( av.get_stamps(), av.get_values() )
            legend.append( name )

        for name in self.avNameList:
            if ( True == self.avAvgFlagDict[name] ):
                av = self.AV[name]

                ax.plot( av.get_stamps(), av.get_avg() )

                legend.append( name + "_avg" )
        
        ax.legend(legend)
        ax.set_title( self.title )
        ax.set_xlabel( self.xlabel )
        ax.set_ylabel( self.ylabel )

        fig.savefig(outDir + "/" + prefix + self.title + suffix + ".png")
        plt.close(fig)

class VisdomLinePlotter(AccumulatedValuePlotter):
    # Class/Static variables.
    vis = None
    visStartUpSec = 1

    def __init__(self, name, av, avNameList, avAvgFlagList = None):
        super(VisdomLinePlotter, self).__init__(name, av, avNameList, avAvgFlagList)

        self.count         = 0
        self.minPlotPoints = 2

        self.visLine = None

    def initialize(self):
        if ( VisdomLinePlotter.vis is not None ):
            print("visdom already initialized.")
            return

        VisdomLinePlotter.vis = Visdom(server = 'http://localhost', port = 8097)

        while not VisdomLinePlotter.vis.check_connection() and VisdomLinePlotter.visStartUpSec > 0:
            time.sleep(0.1)
            VisdomLinePlotter.visStartUpSec -= 0.1
        assert VisdomLinePlotter.vis.check_connection(), 'No connection could be formed quickly'

        print("VisdomLinePlotter initialized.")

    def get_vis(self):
        return VisdomLinePlotter.vis
    
    def is_initialized(self):
        vis = self.get_vis()

        if ( vis is None ):
            return False
        else:
            return True

    def update(self):
        # Check if Visdom is initialized.
        if ( False == self.is_initialized() ):
            exp = WFException("Visdom has not been initialized yet.", "update")
            raise(exp)

        # Gather the data.
        # nLines = len( self.avNameList )
        nMaxPoints = 0

        for name in self.avNameList:
            # Find the AccumulatedVariable object.
            av = self.AV[name]
            nPoints = av.get_num_values()

            if ( nPoints > nMaxPoints ):
                nMaxPoints = nPoints
        
        if ( nMaxPoints < self.minPlotPoints ):
            # Not enough points to plot, do nothing.
            return
        
        # Enough points to plot.
        # Get the points to be ploted.
        nameList = []
        for name in self.avNameList:
            av = self.AV[name]
            lastIdx = self.plotIndexDict[name]
            pointsInAv = av.get_num_values()

            if ( pointsInAv - 1 > lastIdx and 0 != pointsInAv ):
                nameList.append(name)

        if ( 0 == len( nameList ) ):
            # No update actions should be performed.
            return

        # Retreive the Visdom object.
        vis = self.get_vis()

        for i in range( len(nameList) ):
            name    = nameList[i]
            av      = self.AV[name]
            lastIdx = self.plotIndexDict[name]

            x = np.array( av.get_stamps()[ lastIdx + 1 : ] )
            
            if ( self.visLine is None ):
                # Create the Visdom object.
                self.visLine = vis.line(\
                    X = x,\
                    Y = np.array( av.get_values()[ lastIdx + 1 : ] ),\
                    name = name,\
                    opts = dict(\
                        showlegend = True,\
                        title = self.title,\
                        xlabel = self.xlabel,\
                        ylabel = self.ylabel,\
                        margintop=30 \
                    )\
                )
            else:
                # Append data to self.visLine.
                vis.line(\
                    X = x,\
                    Y = np.array( av.get_values()[ lastIdx + 1 : ] ),\
                    win = self.visLine,\
                    name = name,\
                    update = "append",\
                    opts = dict(\
                        showlegend = True \
                    )\
                )

        for i in range( len(nameList) ):
            name    = nameList[i]
            av      = self.AV[name]
            lastIdx = self.plotIndexDict[name]

            # Average line.
            if ( True == self.avAvgFlagDict[name] ):
                vis.line(\
                    X = np.array( av.get_stamps()[ lastIdx + 1 : ] ),\
                    Y = np.array( self.AV[name].get_avg()[ self.plotIndexDict[name] + 1 : ] ),\
                    win = self.visLine,\
                    name = name + "_avg",\
                    update = "append",\
                    opts = dict(\
                        showlegend = True \
                    )\
                )

            # Update the self.plotIndexDict.
            self.plotIndexDict[name] = self.AV[name].get_num_values() - 1
        
        self.count += 1

class WorkFlow(object):
    # Dash object.
    dashAppThread = None

    def __init__(self, workingDir, prefix = "", suffix = "", logFilename = None):
        self.workingDir = workingDir # The working directory.
        self.prefix = prefix
        self.suffix = suffix

        if ( not os.path.isdir(self.workingDir) ):
            os.makedirs( self.workingDir )

        self.isInitialized = False

        # Accumulated value dictionary.
        self.AV = {"loss": AccumulatedValue("loss")}

        # Accumulated value Plotter.
        # self.AVP should be an object of class AccumulatedValuePlotter.
        self.AVP = [] # The child class is responsible to populate this member.

        self.verbose = False

        if ( logFilename is not None ):
            self.logFilename = logFilename
        else:
            self.logFilename = "wf.log"
        
        # Logger.
        # logging.basicConfig(datefmt = '%m/%d/%Y %I:%M:%S')
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        streamHandler = logging.StreamHandler(sys.stdout)
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

        # Dash thread object.
        if ( WorkFlow.dashAppThread is None ):
            WorkFlow.dashAppThread = DashThread("Dash", DASH_APP)

        self.logger.info("WorkFlow created.")

    def add_accumulated_value(self, name, avgWidth = 2):
        # Check if there is alread an ojbect which has the same name.
        if ( name in self.AV.keys() ):
            # This is an error.
            desc = "There is already an object registered as \"%s\"." % (name)
            exp = WFException(desc, "add_accumulated_value")
            raise(exp)
        
        # Name is new. Create a new AccumulatedValue object.
        self.AV[name] = AccumulatedValue(name, avgWidth)

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

        # Initialize AVP.
        if ( len(self.AVP) > 0 ):
            self.AVP[0].initialize()
            self.logger.info("AVP initialized.")

        # Create Dash thread.
        WorkFlow.dashAppThread.start()

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
        
        # Write the accumulated values.
        self.write_accumulated_values()
        self.draw_accumulated_values()

        self.logger.info("Accumulated values are written to %s." % (self.workingDir + "/AccumulatedValues"))

        # Dash thread.
        WorkFlow.dashAppThread.join()

        self.isInitialized = False

        self.debug_print("finalize() get called.")

    def plot_accumulated_values(self):
        if ( 0 == len(self.AVP) ):
            return

        for avp in self.AVP:
            avp.update()

    def write_accumulated_values(self, outDir = None):
        if ( outDir is None ):
            outDir = self.workingDir + "/AccumulatedValues"

        if ( False == os.path.isdir( outDir ) ):
            os.makedirs( outDir )

        for av in self.AV.itervalues():
            av.dump(outDir, self.prefix, self.suffix)

    def draw_accumulated_values(self, outDir = None):
        if ( outDir is None ):
            outDir = self.workingDir + "/AccumulatedValues"

        if ( False == os.path.isdir( outDir ) ):
            os.makedirs( outDir )

        for avp in self.AVP:
            avp.write_image(outDir, self.prefix, self.suffix)

    def is_initialized(self):
        return self.isInitialized

    def debug_print(self, msg):
        if ( True == self.verbose ):
            print(msg)
