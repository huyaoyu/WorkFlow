
from __future__ import print_function

import os
import torch
import os
import WorkFlow

class TorchFlow(WorkFlow.WorkFlow):
    """Add pytorch support based on WorkFlow.WorkFlow"""
    def __init__(self, workingDir, prefix = "", suffix = "", disableStreamLogger = False):
        super(TorchFlow, self).__init__(workingDir, prefix, suffix, None, disableStreamLogger)
    
    # Overload the function initialize().
    def initialize(self):
        super(TorchFlow, self).initialize()

    # Overload the function train().
    def train(self):
        super(TorchFlow, self).train()

    # Overload the function test().
    def test(self):
        super(TorchFlow, self).test()

    # Overload the function finalize().
    def finalize(self):
        super(TorchFlow, self).finalize()

    # ========== Class specific member functions. ==========
    def load_model(self, model, modelname):
        preTrainDict = torch.load(modelname)
        model_dict = model.state_dict()
        # print 'preTrainDict:',preTrainDict.keys()
        # print 'modelDict:',model_dict.keys()
        preTrainDict = {k:v for k,v in preTrainDict.items() if k in model_dict}
        for item in preTrainDict:
            print('  Load pretrained layer: ',item )
        model_dict.update(preTrainDict)
        model.load_state_dict(model_dict)
        return model

    def save_model(self, model, modelname):
        modelname = self.prefix + modelname + self.suffix + '.pkl'
        torch.save(model.state_dict(), os.path.join(self.modeldir, modelname))
