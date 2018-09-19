# -*- coding: utf-8 -*-
'''
Created on Tue Sep 18 10:34:21 2018

@author:
    
    Visa Suomi
    Turku University Hospital
    September 2018
    
@description:
    
    This code is used to classify (using softmax) the treatability of uterine 
    fibroids before HIFU therapy based on their pre-treatment parameters
    
'''

#%% clear variables

%reset -f
%clear

#%% import necessary libraries

#import math

from IPython import display
#from matplotlib import cm
#from matplotlib import gridspec
#from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
#from sklearn import metrics
from sklearn import model_selection
import tensorflow as tf
#from tensorflow.python.data import Dataset
import time

#from train_linear_classification_model import train_linear_classification_model
from train_neural_network_softmax_classification_model import train_neural_network_softmax_classification_model
from scale_features import scale_features
from save_load_variables import save_load_variables

#%% define logging and data display format

tf.logging.set_verbosity(tf.logging.ERROR)
pd.options.display.max_rows = 10
pd.options.display.float_format = '{:.1f}'.format

#%% read data

fibroid_dataframe = pd.read_csv(r'C:\Users\visa\Documents\TYKS\Machine learning\Uterine fibroid\test_data.csv', sep = ',')

#%% plot NPV histogram

fibroid_dataframe['NPV_percent'].hist(bins = 20)

#%% categorise NPV into classes according to bins

NPV_bins = [-1, 20, 60, 80, 100]
fibroid_dataframe['NPV_class'] = fibroid_dataframe['NPV_percent'].apply(lambda x: pd.cut(x, NPV_bins, labels = False))

#%% format data

# randomise the data

fibroid_dataframe = fibroid_dataframe.reindex(np.random.permutation(fibroid_dataframe.index))

# examine data

print('\nFirst five entries of the data:\n')
display.display(fibroid_dataframe.head())
print('\nSummary of the data:\n')
display.display(fibroid_dataframe.describe())

#%% divide data into training and validation sets

# stratified splitting for unbalanced datasets

training_set, validation_set = model_selection.train_test_split(fibroid_dataframe, test_size = 0.25,
                                              stratify = fibroid_dataframe['NPV_class'])

#%% display correlation matrix to help select suitable features

print('\nCorrelation matrix:\n')
display.display(training_set.corr())

#%% select features and targets

training_features = training_set[['Age', 'History_of_pregnancy',
                                  'Subcutaneous_fat_thickness', 'Front-back_distance', 'Abdominal_scars',
                                  'Fibroid_distance', 'Type_I', 'Type_II', 'Type_III',
                                  'Fibroid_volume']]
#training_features = training_set[['white', 'black', 'asian', 'Age', 'Weight', 'History_of_pregnancy',
#                                  'Live_births', 'C-section', 'esmya', 'open_myomectomy', 
#                                  'laprascopic_myomectomy', 'hysteroscopic_myomectomy',
#                                  'Subcutaneous_fat_thickness', 'Front-back_distance', 'Abdominal_scars',
#                                  'bleeding', 'pain', 'mass', 'urinary', 'infertility',
#                                  'Fibroid_size', 'Fibroid_distance', 'intramural', 'subserosal', 
#                                  'submucosal', 'anterior', 'posterior', 'lateral', 'fundus',
#                                  'anteverted', 'retroverted', 'Type_I', 'Type_II', 'Type_III',
#                                  'Fibroid_volume']]
training_targets = training_set[['NPV_class']]

validation_features = validation_set[['Age', 'History_of_pregnancy',
                                      'Subcutaneous_fat_thickness', 'Front-back_distance', 'Abdominal_scars',
                                      'Fibroid_distance', 'Type_I', 'Type_II', 'Type_III',
                                      'Fibroid_volume']]
#validation_features = validation_set[['white', 'black', 'asian', 'Age', 'Weight', 'History_of_pregnancy',
#                                  'Live_births', 'C-section', 'esmya', 'open_myomectomy', 
#                                  'laprascopic_myomectomy', 'hysteroscopic_myomectomy',
#                                  'Subcutaneous_fat_thickness', 'Front-back_distance', 'Abdominal_scars',
#                                  'bleeding', 'pain', 'mass', 'urinary', 'infertility',
#                                  'Fibroid_size', 'Fibroid_distance', 'intramural', 'subserosal', 
#                                  'submucosal', 'anterior', 'posterior', 'lateral', 'fundus',
#                                  'anteverted', 'retroverted', 'Type_I', 'Type_II', 'Type_III',
#                                  'Fibroid_volume']]
validation_targets = validation_set[['NPV_class']]

#%% scale features

scaling_type = 'z-score'
scaled_training_features = scale_features(training_features, scaling_type)
scaled_validation_features = scale_features(validation_features, scaling_type)

#%% create weight columns

weight_column = None

#%% train using neural network classification model function

# define parameters

learning_rate = 0.001
steps = 3000
batch_size = 5
hidden_units = [25]
n_classes = 4
dropout = 0.3
batch_norm = True
optimiser = 'Adam'
save_model = True

# directory for saving the model

if save_model is True:
    timestr = time.strftime('%Y%m%d-%H%M%S')
    model_dir = 'models\\' + timestr
else:
    model_dir = None

# train the model

dnn_classifier, training_predictions, validation_predictions = train_neural_network_softmax_classification_model(
    learning_rate = learning_rate,
    steps = steps,
    batch_size = batch_size,
    hidden_units = hidden_units,
    n_classes = n_classes,
    weight_column = weight_column,
    dropout = dropout,
    batch_norm = batch_norm,
    optimiser = optimiser,
    model_dir = model_dir,
    training_features = scaled_training_features,
    training_targets = training_targets,
    validation_features = scaled_validation_features,
    validation_targets = validation_targets)

# save variables

if save_model is True:

    variables_to_save = {'learning_rate': learning_rate,
                         'steps': steps,
                         'batch_size': batch_size,
                         'hidden_units': hidden_units,
                         'n_classes': n_classes,
                         'weight_column': weight_column,
                         'dropout': dropout,
                         'batch_norm': batch_norm,
                         'optimiser': optimiser,
                         'model_dir': model_dir,
                         'training_set': training_set,
                         'training_features': training_features,
                         'scaled_training_features': scaled_training_features,
                         'training_targets': training_targets,
                         'training_predictions': training_predictions,
                         'validation_set': validation_set,
                         'validation_features': validation_features,
                         'scaled_validation_features': scaled_validation_features,
                         'validation_targets': validation_targets,
                         'validation_predictions': validation_predictions,
                         'fibroid_dataframe': fibroid_dataframe,
                         'split_ratio': split_ratio,
                         'timestr': timestr,
                         'scaling_type': scaling_type,
                         'NPV_bins': NPV_bins}
    
    save_load_variables(model_dir, variables_to_save, 'save')
