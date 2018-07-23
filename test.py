from workflow import WorkFlow

def print_delimeter(c = "=", n = 20, title = None):
    if ( title is None ):
        for i in range(n):
            print(c, end = "")
    else:
        halfN = (int)(n / 2.0)

        for i in range(halfN):
            print(c, end = "")

        print(" %s " % (title), end = "")

        for i in range(halfN):
            print(c, end = "")
    
    print("")

# Template for custom WorkFlow object.
class MyWF(WorkFlow.WorkFlow):
    def __init__(self, workingDir):
        super(MyWF, self).__init__(workingDir)

        # Create the AccumulatedObjects.
        self.add_accumulated_value("lossTest")
        # This should raise an exception.
        # self.add_accumulated_value("loss")

        # Custom member variables.
        self.countTrain = 0
        self.countTest  = 0

    # Overload the function initialize().
    def initialize(self):
        super(MyWF, self).initialize()

        # Custom code.
        print("Initialized.")

    # Overload the function train().
    def train(self):
        super(MyWF, self).train()

        # Custom code.
        print("Train loop #%d" % self.countTrain)

        # Test the existance of an AccumulatedValue object.
        if ( True == self.have_accumulated_value("loss") ):
            self.AV["loss"].push_back(0.01, self.countTrain)
        else:
            print("Could not find \"loss\"")

        self.countTrain += 1

        print("Trained.")

    # Overload the function test().
    def test(self):
        super(MyWF, self).test()

        # Custom code.
        # Test the existance of an AccumulatedValue object.
        if ( True == self.have_accumulated_value("lossTest") ):
            self.AV["lossTest"].push_back(0.01, self.countTest)
        else:
            print("Could not find \"lossTest\"")

        print("Tested.")

    # Overload the function finalize().
    def finalize(self):
        super(MyWF, self).finalize()

        # Custom code.
        print("Finalized.")

if __name__ == "__main__":
    print("Hello WorkFlow.")

    print_delimeter(title = "Before initialization.")

    # Instanciate an object for MyWF.

    wf = MyWF("/tmp/WorkFlowDir")

    wf.verbose = True

    try:
        wf.train()
    except WorkFlow.WFException as exp:
        print(exp.describe())

    try:
        wf.test()
    except WorkFlow.WFException as exp:
        print(exp.describe())

    try:
        wf.finalize()
    except WorkFlow.WFException as exp:
        print(exp.describe())

    print_delimeter(title = "Initialize.")

    wf.initialize()

    try:
        wf.initialize()
    except WorkFlow.WFException as exp:
        print(exp.describe())

    print_delimeter(title = "Loop.")

    for i in range(5):
        wf.train()

    print_delimeter(title = "Test and finalize.")

    wf.test()
    wf.finalize()

    print_delimeter(title = "Accumulated values.")

    wf.AV["loss"].show_raw_data()

    print_delimeter()

    wf.AV["lossTest"].show_raw_data()

    print("Done.")
