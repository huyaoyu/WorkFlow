#! /usr/bin/python

from __future__ import print_function

import math
import time

from workflow import WorkFlow

def print_delimeter(c = "=", n = 20, title = "", leading = "\n", ending = "\n"):
    d = [c for i in range(n/2)]

    if ( 0 == len(title) ):
        s = "".join(d) + "".join(d)
    else:
        s = "".join(d) + " " + title + " " + "".join(d)

    print("%s%s%s" % (leading, s, ending))

# Template for custom WorkFlow object.
class MyWF(WorkFlow.WorkFlow):
    def __init__(self, workingDir, prefix = "", suffix = ""):
        super(MyWF, self).__init__(workingDir, prefix, suffix)

        # === Create the AccumulatedObjects. ===
        self.add_accumulated_value("loss2", 10)
        self.add_accumulated_value("lossLeap")
        self.add_accumulated_value("testAvg1", 10)
        self.add_accumulated_value("testAvg2", 20)
        self.add_accumulated_value("lossTest")
        # This should raise an exception.
        # self.add_accumulated_value("loss")

        # === Create a AccumulatedValuePlotter object for ploting. ===
        avNameList    = ["loss", "loss2", "lossLeap"]
        avAvgFlagList = [  True,   False,      True ]
        self.AVP.append(\
            WorkFlow.VisdomLinePlotter(\
                "Combined", self.AV, avNameList, avAvgFlagList)\
        )

        self.AVP.append(\
            WorkFlow.VisdomLinePlotter(\
                "loss", self.AV, ["loss"])\
        )

        self.AVP.append(\
            WorkFlow.VisdomLinePlotter(\
                "losse", self.AV, ["loss2"], [True])\
        )

        self.AVP.append(\
            WorkFlow.VisdomLinePlotter(\
                "lossLeap", self.AV, ["lossLeap"], [True])\
        )
        self.AVP[-1].title = "Loss Leap"

        self.AVP.append(\
            WorkFlow.VisdomLinePlotter(\
                "testAvg1", self.AV, ["testAvg1"], [True])\
        )

        self.AVP.append(\
            WorkFlow.VisdomLinePlotter(\
                "testAvg2", self.AV, ["testAvg2"], [True])\
        )

        # === Custom member variables. ===
        self.countTrain = 0
        self.countTest  = 0

    # Overload the function initialize().
    def initialize(self):
        super(MyWF, self).initialize()

        # === Custom code. ===
        self.logger.info("Initialized.")

    # Overload the function train().
    def train(self):
        super(MyWF, self).train()

        # === Custom code. ===
        self.logger.info("Train loop #%d" % self.countTrain)

        # Test the existance of an AccumulatedValue object.
        if ( True == self.have_accumulated_value("loss") ):
            self.AV["loss"].push_back(math.sin( self.countTrain*0.1 ), self.countTrain*0.1)
        else:
            self.logger.info("Could not find \"loss\"")

        # Directly access "loss2" without existance test.
        self.AV["loss2"].push_back(math.cos( self.countTrain*0.1 ), self.countTrain*0.1)

        # lossLeap.
        if ( self.countTrain % 10 == 0 ):
            self.AV["lossLeap"].push_back(\
                math.sin( self.countTrain*0.1 + 0.25*math.pi ),\
                self.countTrain*0.1)

        # testAvg.
        self.AV["testAvg1"].push_back( 0.5, self.countTrain )

        if ( self.countTrain < 50 ):
            self.AV["testAvg2"].push_back( self.countTrain, self.countTrain )
        else:
            self.AV["testAvg2"].push_back( 50, self.countTrain )

        if ( self.countTrain % 10 == 0 ):
            self.write_accumulated_values()

        self.countTrain += 1

        # Plot accumulated values.
        self.plot_accumulated_values()

        self.logger.info("Trained.")

        time.sleep(0.05)

    # Overload the function test().
    def test(self):
        super(MyWF, self).test()

        # === Custom code. ===
        # Test the existance of an AccumulatedValue object.
        if ( True == self.have_accumulated_value("lossTest") ):
            self.AV["lossTest"].push_back(0.01, self.countTest)
        else:
            self.logger.info("Could not find \"lossTest\"")

        self.logger.info("Tested.")

    # Overload the function finalize().
    def finalize(self):
        super(MyWF, self).finalize()

        # === Custom code. ===
        self.logger.info("Finalized.")

if __name__ == "__main__":
    print("Hello WorkFlow.")

    print_delimeter(title = "Before initialization." )

    try:
        # Instantiate an object for MyWF.
        wf = MyWF("./", prefix = "1_1_", suffix = "")
        wf.verbose = True

        # Initialization.
        print_delimeter(title = "Initialize.")
        wf.initialize()

        # Training loop.
        print_delimeter(title = "Loop.")

        for i in range(100):
            wf.train()

        # Test and finalize.
        print_delimeter(title = "Test and finalize.")

        wf.test()
        wf.finalize()

        # # Show the accululated values.
        # print_delimeter(title = "Accumulated values.")
        # wf.AV["loss"].show_raw_data()

        # print_delimeter()
        # wf.AV["lossLeap"].show_raw_data()

        # print_delimeter()
        # wf.AV["lossTest"].show_raw_data()
    except WorkFlow.WFException as e:
        print( e.describe() )

    print("Done.")
