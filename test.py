#! /usr/bin/python

from __future__ import print_function

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
    def __init__(self, workingDir):
        super(MyWF, self).__init__(workingDir, prefix = "", suffix = "")

        # === Create the AccumulatedObjects. ===
        self.add_accumulated_value("lossTest")
        # This should raise an exception.
        # self.add_accumulated_value("loss")

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
            self.AV["loss"].push_back(0.01, self.countTrain)
        else:
            self.logger.info("Could not find \"loss\"")

        self.countTrain += 1

        self.logger.info("Trained.")

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

    print_delimeter(title = "Before initialization.")

    # Instantiate an object for MyWF.

    wf = MyWF("/tmp/WorkFlowDir")

    wf.verbose = True

    # Trigger an exception.
    try:
        wf.train()
    except WorkFlow.WFException as exp:
        print(exp.describe())

    # Trigger an exception.
    try:
        wf.test()
    except WorkFlow.WFException as exp:
        print(exp.describe())

    # Trigger an exception.
    try:
        wf.finalize()
    except WorkFlow.WFException as exp:
        print(exp.describe())

    # Actual initialization.
    print_delimeter(title = "Initialize.")

    wf.initialize()

    # Trigger an exception.
    try:
        wf.initialize()
    except WorkFlow.WFException as exp:
        print(exp.describe())

    # Training loop.
    print_delimeter(title = "Loop.")

    for i in range(5):
        wf.train()

    # Test and finalize.
    print_delimeter(title = "Test and finalize.")

    wf.test()
    wf.finalize()

    # Show the accululated values.
    print_delimeter(title = "Accumulated values.")

    wf.AV["loss"].show_raw_data()

    print_delimeter()

    wf.AV["lossTest"].show_raw_data()

    print("Done.")
