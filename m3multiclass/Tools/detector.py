#!/usr/bin/python
#Copyright 2015 CVC-UAB

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

__author__ = "Miquel Ferrarons, David Vazquez"
__copyright__ = "Copyright 2015, CVC-UAB"
__credits__ = ["Miquel Ferrarons", "David Vazquez"]
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Miquel Ferrarons"

import os
import feature_extractor
import pickle
import match_annotations
import numpy as np
from skimage import io
from skimage.util import pad
from skimage.transform import pyramid_gaussian
from skimage.util.shape import view_as_windows
import skimage.util as util
import math
import nms
import time
import Config as cfg
import match_annotations


def testImage(imagePath):

    fileList = os.listdir(cfg.modelRootPath)

    # Filter all model files
    modelsList = filter(lambda element: '.model' in element, fileList)

    # Filter our specific feature method
    currentModel = cfg.modelFeatures
    currentModelsList = filter(lambda element: currentModel in element, modelsList)

    models = []

    for modelname in currentModelsList:

        file = open(cfg.modelRootPath + modelname, 'r')
        svc = pickle.load(file)
        models.append(svc)

        file.close()

    image = io.imread(imagePath, as_grey=True)
    image = util.img_as_ubyte(image) #Read the image as bytes (pixels with values 0-255)

    feats = feature_extractor.extractFeatures(image, imagePath)
    max_score = -2
    counter = 0
    model_index = 14 #Backgorund

    #Obtain prediction score for each model
    for model in models:

        decision_func = model.decision_function(feats)
        score = decision_func[0]
        if score > max_score:
            max_score = score
            modelname = currentModelsList[counter]
            model_index = modelname.split('_')
            model_index = model_index[2]
            model_index = model_index[0:len(model_index)-6]     #Parse class index from model name
        counter += 1

    print model_index
    #Condition by intuition: If score is too low is background?
    # if max_score < cfg.min_score:
    #     model_index = cfg.index_background   #Assign background index

    return model_index



def testFolder(inputfolder, outputfolder):

    start_time = time.time()

    fileList = os.listdir(inputfolder)
    imagesList = filter(lambda element: '.jpg' in element, fileList)

    gt = []
    predictions = []

    print 'Start processing '+inputfolder
    for filename in imagesList:
        imagepath = inputfolder + '/' + filename
        print 'Processing '+imagepath

        #Test the current image
        prediction = testImage(imagepath)
        predictions.append(prediction)

        #Load annotation from filename

        #Own crops from detector
        annotation = filename.split('.')
        annotation = annotation[len(annotation)-2]
        annotation = match_annotations.matchAnnotations(annotation)
        gt.append(annotation)

        #Pre-annotated crops
        # annotation = filename.split('_')
        # annotation = annotation[1]
        # gt.append(annotation[0:len(annotation)-4])

    #Store the result in a dictionary
    result = dict()
    result['gt'] = gt
    result['predictions'] = predictions

    #Save the features to a file using pickle
    outputFile = open(outputfolder+'/'+'-'.join(cfg.featuresToExtract)+'_'+cfg.model+'.results', "wb")
    pickle.dump(result, outputFile)
    outputFile.close()

    print("FINISH PROCESS  --- %s seconds ---" % (time.time() - start_time))
