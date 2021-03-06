# -*- coding: utf-8 -*-
'''
Created on Fri Jan 18 10:59:43 2019

@author:
    
    Visa Suomi
    Turku University Hospital
    January 2019
    
@description:
    
    This code is used for feature selection for different classification models
    
'''

#%% clear variables

%reset -f
%clear

#%% import necessary libraries

import os
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.svm import SVC
#from sklearn.feature_selection import SelectKBest, chi2, f_classif, mutual_info_classif
#from sklearn.utils.class_weight import compute_class_weight
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.metrics import f1_score

from skfeature.function.similarity_based import fisher_score
from skfeature.function.similarity_based import reliefF
from skfeature.function.similarity_based import trace_ratio
from skfeature.function.statistical_based import gini_index
from skfeature.function.statistical_based import chi_square                     # same as chi2
from skfeature.function.statistical_based import f_score                        # same as f_classif
#from skfeature.function.statistical_based import CFS
#from skfeature.function.statistical_based import t_score                        # only for binary
from skfeature.function.information_theoretical_based import JMI
from skfeature.function.information_theoretical_based import CIFE
from skfeature.function.information_theoretical_based import DISR
from skfeature.function.information_theoretical_based import MIM
from skfeature.function.information_theoretical_based import CMIM
from skfeature.function.information_theoretical_based import ICAP
from skfeature.function.information_theoretical_based import MRMR
from skfeature.function.information_theoretical_based import MIFS

from save_load_variables import save_load_variables

#%% define logging and data display format

pd.options.display.max_rows = 10
pd.options.display.float_format = '{:.1f}'.format
pd.options.mode.chained_assignment = None                                       # disable imputation warnings

#%% read data

dataframe = pd.read_csv(r'fibroid_dataframe.csv', sep = ',')

#%% calculate nan percent for each label

nan_percent = pd.DataFrame(dataframe.isnull().mean() * 100, columns = ['NaN ratio'])

#%% display NPV histogram

dataframe['NPV ratio'].hist(bins = 20)

#%% categorise NPV into classes according to bins

NPV_bins = [-1, 29.9, 80, 100]
dataframe['NPV class'] = dataframe[['NPV ratio']].apply(lambda x: pd.cut(x, NPV_bins, labels = False))

#%% define feature and target labels

feature_labels = ['White', 
                  'Black', 
                  'Asian', 
                  'Age', 
                  'Weight', 
                  'Height', 
                  'Gravidity', 
                  'Parity',
                  'Previous pregnancies', 
                  'Live births', 
                  'C-section', 
                  'Esmya', 
                  'Open myomectomy', 
                  'Laparoscopic myomectomy', 
                  'Hysteroscopic myomectomy',
                  'Embolisation', 
                  'Subcutaneous fat thickness', 
                  'Front-back distance', 
                  'Abdominal scars', 
                  'Bleeding', 
                  'Pain', 
                  'Mass', 
                  'Urinary', 
                  'Infertility',
                  'Fibroid diameter', 
                  'Fibroid distance', 
                  'Intramural', 
                  'Subserosal', 
                  'Submucosal', 
                  'Anterior', 
                  'Posterior', 
                  'Lateral', 
                  'Fundus',
                  'Anteverted', 
                  'Retroverted', 
                  'Type I', 
                  'Type II', 
                  'Type III',
#                  'ADC',
                  'Fibroid volume'
                  ]

target_label = ['NPV class']

#%% define parameters for iteration

# define number of iterations

n_iterations = 200

# define split ratio for training and testing sets

split_ratio = 0.2

# define scaling type ('log', 'minmax', 'standard' or None)

scaling_type = 'log'

# define number of features

n_features = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]

# define scorer methods

methods =   ['FISH', 
             'RELF', 
             'TRAC',
             'GINI', 
             'CHI2', 
             'FSCR',
             'DISR', 
             'CMIM',
             'ICAP',
             'JMI',
             'CIFE',
             'MIM',
             'MRMR',
             'MIFS'
             ]

# define scorer functions

scorers = [fisher_score.fisher_score, 
           reliefF.reliefF,
           trace_ratio.trace_ratio,
           gini_index.gini_index,
           chi_square.chi_square, 
           f_score.f_score,
           DISR.disr, 
           CMIM.cmim,
           ICAP.icap,
           JMI.jmi,
           CIFE.cife,
           MIM.mim,
           MRMR.mrmr,
           MIFS.mifs
           ]

# define scorer rankers (for scikit-feature only)

rankers = [fisher_score.feature_ranking, 
           reliefF.feature_ranking,
           None,
           gini_index.feature_ranking,
           chi_square.feature_ranking,
           f_score.feature_ranking,
           None,
           None,
           None,
           None,
           None,
           None, 
           None,
           None
           ]

# define parameters for parameter search

grid_param =    {
                'kernel': ['rbf'], 
                'C': list(np.logspace(-1, 4, 6)),
                'gamma': list(np.logspace(-2, 4, 7)),
                'random_state': [None]
                }

# define data imputation values

impute_labels = ['Height', 
                 'Gravidity'
                 ]

# define classification model

max_iter = 200000
class_weight = 'balanced'

clf_model = SVC(probability = True, class_weight = class_weight, cache_size = 4000,
                max_iter = max_iter)

# define parameter search method

cv = 10
scoring = 'f1_micro'
    
clf_grid = GridSearchCV(clf_model, grid_param, n_jobs = -1, cv = cv, 
                        scoring = scoring, refit = True, iid = False)

# initialise variables

clf_results = pd.DataFrame()
feature_rankings = pd.DataFrame()
k = len(feature_labels)

#%% start the iteration

timestr = time.strftime('%Y%m%d-%H%M%S')
start_time = time.time()

for iteration in range(0, n_iterations):
    
    # define random state

    random_state = np.random.randint(0, 10000)
    
    # assign random state to grid parameters
    
    grid_param['random_state'] = [random_state]
    
    # print progress
    
    print('Iteration %d with random state %d at %.1f min' % (iteration, random_state, 
                                                             ((time.time() - start_time) / 60)))
    
    # randomise and divive data for cross-validation
    
    training_set, testing_set = train_test_split(dataframe, test_size = split_ratio,
                                                 stratify = dataframe[target_label],
                                                 random_state = random_state)
    
    impute_values = {}
    
    for label in impute_labels:
        
        if label in {'Height', 'ADC'}:
            
            impute_values[label] = training_set[label].mean()
            
            training_set[label] = training_set[label].fillna(impute_values[label])
            testing_set[label] = testing_set[label].fillna(impute_values[label])
            
        else:
            
            impute_values[label] = training_set[label].mode()[0]
            
            training_set[label] = training_set[label].fillna(impute_values[label])
            testing_set[label] = testing_set[label].fillna(impute_values[label])
            
    del label
    
    # define features and targets
    
    training_features = training_set[feature_labels]
    testing_features = testing_set[feature_labels]
    
    training_targets = training_set[target_label]
    testing_targets = testing_set[target_label]
    
    # scale features
       
    if scaling_type == 'log':
        
        training_features = np.log1p(training_features)
        testing_features = np.log1p(testing_features)
        
    elif scaling_type == 'minmax':
        
        scaler = MinMaxScaler(feature_range = (0, 1)) 
        training_features = pd.DataFrame(scaler.fit_transform(training_features),
                                         columns = training_features.columns,
                                         index = training_features.index)
        testing_features = pd.DataFrame(scaler.transform(testing_features),
                                        columns = testing_features.columns,
                                        index = testing_features.index)
        
    elif scaling_type == 'standard':
        
        scaler = StandardScaler() 
        training_features = pd.DataFrame(scaler.fit_transform(training_features),
                                         columns = training_features.columns,
                                         index = training_features.index)
        testing_features = pd.DataFrame(scaler.transform(testing_features),
                                        columns = testing_features.columns,
                                        index = testing_features.index)
    
    # find k best features for each feature selection method
    
    k_features = pd.DataFrame(index = range(0, k), columns = methods)
    
    for scorer, ranker, method in zip(scorers, rankers, methods):
        
        if method in ('DISR', 'CMIM', 'ICAP', 'JMI', 'CIFE', 'MIM', 'MRMR', 'MIFS', 'TRAC'):
            
            indices, _, _ = scorer(training_features.values, training_targets.values[:, 0], n_selected_features = k)
            k_features[method] = pd.DataFrame(training_features.columns.values[indices], columns = [method])
            
            del indices
        
        else:
            
            scores = scorer(training_features.values, training_targets.values[:, 0])
            indices = ranker(scores)
            k_features[method] = pd.DataFrame(training_features.columns.values[indices[0:k]], columns = [method])
            
            del scores, indices
            
    del scorer, ranker, method
    
    # calculate feature scores
    
    k_rankings = pd.DataFrame(k_features.T.values.argsort(1),
                              columns = np.sort(k_features.iloc[:, 0].values),
                              index = k_features.columns)
    k_rankings['method'] = k_rankings.index
    k_rankings['iteration'] = iteration
    k_rankings['random_state'] = random_state
    feature_rankings = feature_rankings.append(k_rankings, sort = False, ignore_index = True)
    
    del k_rankings
    
    # train model using parameter search

    for n in n_features:
        for method in methods:
            
            # fit parameter search
        
            clf_fit = clf_grid.fit(training_features[k_features[method][0:n]].values, training_targets.values[:, 0])
            
            # calculate predictions
            
            testing_predictions = clf_fit.predict(testing_features[k_features[method][0:n]].values)
            test_score = f1_score(testing_targets.values[:, 0], testing_predictions, average = scoring[3:])
            
            # save results
            
            df = pd.DataFrame(clf_fit.best_params_, index = [0])
            df['method'] = method
            df['validation_score'] = clf_fit.best_score_
            df['test_score'] = test_score
            df['n_features'] = n
            df['iteration'] = iteration
            df['random_state'] = random_state
            clf_results = clf_results.append(df, sort = False, ignore_index = True)
            
            del clf_fit, testing_predictions, test_score, df
    
    del n, method
    del k_features, random_state, impute_values
    del training_set, training_features, training_targets
    del testing_set, testing_features, testing_targets
    
del iteration

end_time = time.time()

print('Total execution time: %.1f min' % ((end_time - start_time) / 60))

#%% calculate summaries

# summarise results

mean_vscores = clf_results.groupby(['method', 'n_features'], as_index = False)['validation_score'].mean()
mean_tscores = clf_results.groupby(['method', 'n_features'])['test_score'].mean().values

std_vscores = clf_results.groupby(['method', 'n_features'])['validation_score'].std().values
std_tscores = clf_results.groupby(['method', 'n_features'])['test_score'].std().values

clf_summary = mean_vscores.copy()
clf_summary['test_score'] = mean_tscores
clf_summary['validation_score_std'] =  std_vscores
clf_summary['test_score_std'] = std_tscores

del mean_vscores, mean_tscores, std_vscores, std_tscores

# calculate heatmaps for test scores, validation scores and feature reankings
    
heatmap_vscore_mean = clf_summary.pivot(index = 'method', columns = 'n_features', values = 'validation_score')
heatmap_vscore_mean.columns = heatmap_vscore_mean.columns.astype(int)

heatmap_tscore_mean = clf_summary.pivot(index = 'method', columns = 'n_features', values = 'test_score')
heatmap_tscore_mean.columns = heatmap_tscore_mean.columns.astype(int)

heatmap_rankings_mean = feature_rankings.groupby(['method'], as_index = False)[feature_labels].mean()
heatmap_rankings_mean = heatmap_rankings_mean.set_index('method')

heatmap_rankings_median = feature_rankings.groupby(['method'], as_index = False)[feature_labels].median()
heatmap_rankings_median = heatmap_rankings_median.set_index('method')

# calculate box plot

feature_boxplot = feature_rankings[feature_labels].melt(var_name = 'feature', value_name = 'ranking')

# calculate top features based on mean and median values

top_features_mean = feature_boxplot.groupby(['feature'], as_index = False)['ranking'].mean()
top_features_mean['std'] = feature_boxplot.groupby(['feature'])['ranking'].std().values
top_features_mean = top_features_mean.sort_values('ranking', ascending = True)
top_features_mean = top_features_mean.reset_index(drop = True)
top_features_mean['method'] = 'TOPN'

top_features_median = feature_boxplot.groupby(['feature'], as_index = False)['ranking'].median()
top_features_median['std'] = feature_boxplot.groupby(['feature'])['ranking'].std().values
top_features_median = top_features_median.sort_values('ranking', ascending = True)
top_features_median = top_features_median.reset_index(drop = True)
top_features_median['method'] = 'TOPN'

#%% train model with only top features

top_results = pd.DataFrame()
random_states = clf_results.random_state.unique()
iteration = 0

time_stamp = time.time()

for random_state in random_states:
    
    # assign random state to grid parameters
    
    grid_param['random_state'] = [random_state]
    
    # print progress
    
    print('Iteration %d with random state %d at %.1f min' % (iteration, random_state, 
                                                             ((time.time() - time_stamp) / 60)))
    
    # randomise and divive data for cross-validation
    
    training_set, testing_set = train_test_split(dataframe, test_size = split_ratio,
                                                 stratify = dataframe[target_label],
                                                 random_state = random_state)
    
    impute_values = {}
    
    for label in impute_labels:
        
        if label in {'Height', 'ADC'}:
            
            impute_values[label] = training_set[label].mean()
            
            training_set[label] = training_set[label].fillna(impute_values[label])
            testing_set[label] = testing_set[label].fillna(impute_values[label])
            
        else:
            
            impute_values[label] = training_set[label].mode()[0]
            
            training_set[label] = training_set[label].fillna(impute_values[label])
            testing_set[label] = testing_set[label].fillna(impute_values[label])
            
    del label
    
    # define features and targets
    
    training_features = training_set[feature_labels]
    testing_features = testing_set[feature_labels]
    
    training_targets = training_set[target_label]
    testing_targets = testing_set[target_label]
    
    # scale features
       
    if scaling_type == 'log':
        
        training_features = np.log1p(training_features)
        testing_features = np.log1p(testing_features)
        
    elif scaling_type == 'minmax':
        
        scaler = MinMaxScaler(feature_range = (0, 1)) 
        training_features = pd.DataFrame(scaler.fit_transform(training_features),
                                         columns = training_features.columns,
                                         index = training_features.index)
        testing_features = pd.DataFrame(scaler.transform(testing_features),
                                        columns = testing_features.columns,
                                        index = testing_features.index)
        
    elif scaling_type == 'standard':
        
        scaler = StandardScaler() 
        training_features = pd.DataFrame(scaler.fit_transform(training_features),
                                         columns = training_features.columns,
                                         index = training_features.index)
        testing_features = pd.DataFrame(scaler.transform(testing_features),
                                        columns = testing_features.columns,
                                        index = testing_features.index)
    
    for n in n_features:
        
        # fit parameter search
            
        clf_fit = clf_grid.fit(training_features[top_features_median['feature'][0:n]].values, training_targets.values[:, 0])
        
        # calculate predictions
        
        testing_predictions = clf_fit.predict(testing_features[top_features_median['feature'][0:n]].values)
        test_score = f1_score(testing_targets.values[:, 0], testing_predictions, average = scoring[3:])
        
        # save results
        
        df = pd.DataFrame(clf_fit.best_params_, index = [0])
        df['method'] = 'TOPN'
        df['validation_score'] = clf_fit.best_score_
        df['test_score'] = test_score
        df['n_features'] = n
        df['iteration'] = iteration
        df['random_state'] = random_state
        top_results = top_results.append(df, sort = False, ignore_index = True)
        
        del clf_fit, testing_predictions, test_score, df
        
    del n
    del impute_values
    del training_set, training_features, training_targets
    del testing_set, testing_features, testing_targets
        
    iteration += 1

print('Total execution time: %.1f min' % ((time.time() - time_stamp) / 60))

del random_state, iteration, time_stamp

#%% calculate top summaries

# summarise results

mean_vscores = top_results.groupby(['method', 'n_features'], as_index = False)['validation_score'].mean()
mean_tscores = top_results.groupby(['method', 'n_features'])['test_score'].mean().values

std_vscores = top_results.groupby(['method', 'n_features'])['validation_score'].std().values
std_tscores = top_results.groupby(['method', 'n_features'])['test_score'].std().values

top_summary = mean_vscores.copy()
top_summary['test_score'] = mean_tscores
top_summary['validation_score_std'] =  std_vscores
top_summary['test_score_std'] = std_tscores

del mean_vscores, mean_tscores, std_vscores, std_tscores

# calculate heatmaps for test scores, validation scores and feature reankings
    
top_vscore_mean = top_summary.pivot(index = 'method', columns = 'n_features', values = 'validation_score')
top_vscore_mean.columns = top_vscore_mean.columns.astype(int)

top_tscore_mean = top_summary.pivot(index = 'method', columns = 'n_features', values = 'test_score')
top_tscore_mean.columns = top_tscore_mean.columns.astype(int)

top_rankings_mean = top_features_mean.pivot(index = 'method', columns = 'feature', values = 'ranking')
top_rankings_median = top_features_median.pivot(index = 'method', columns = 'feature', values = 'ranking')

# append top scores into existing heatmaps

heatmap_vscore_mean = heatmap_vscore_mean.append(top_vscore_mean, sort = True, ignore_index = False)
heatmap_tscore_mean = heatmap_tscore_mean.append(top_tscore_mean, sort = True, ignore_index = False)

heatmap_rankings_mean = heatmap_rankings_mean.append(top_rankings_mean, sort = True, ignore_index = False)
heatmap_rankings_median = heatmap_rankings_median.append(top_rankings_median, sort = True, ignore_index = False)

del top_vscore_mean, top_tscore_mean, top_rankings_mean, top_rankings_median

#%% calculate feature correlations

# correlation matrix

feature_corr = dataframe[feature_labels].corr(method = 'pearson')
method_corr = heatmap_rankings_median.T.corr(method = 'kendall')

# a mask for the upper triangle

feature_corr_mask = np.zeros_like(feature_corr, dtype = np.bool)
feature_corr_mask[np.triu_indices_from(feature_corr_mask)] = True

method_corr_mask = np.zeros_like(method_corr, dtype = np.bool)
method_corr_mask[np.triu_indices_from(method_corr_mask)] = True

#%% plot figures

# define colormap

#cmap = sns.diverging_palette(220, 10, as_cmap = True)
cmap = 'RdBu'

# plot validation and test scores

f1 = plt.figure()
ax = sns.heatmap(heatmap_vscore_mean, cmap = 'Blues', linewidths = 0.5, annot = True, fmt = ".2f")
#ax.set_aspect(1)
plt.ylabel('Feature selection method')
plt.xlabel('Number of features')

f2 = plt.figure()
ax = sns.heatmap(heatmap_tscore_mean, cmap = 'Blues', linewidths = 0.5, annot = True, fmt = ".2f")
#ax.set_aspect(1)
plt.ylabel('Feature selection method')
plt.xlabel('Number of features')

f3 = plt.figure()
ax = sns.lineplot(data = clf_summary, x = 'n_features', y = 'validation_score', 
                  label = 'Validation', ci = 95)
ax = sns.lineplot(data = clf_summary, x = 'n_features', y = 'test_score', 
                  label = 'Test', ci = 95)
ax.grid(True)
ax.xaxis.set_major_locator(ticker.MultipleLocator(2))
ax.autoscale(enable = True, axis = 'x', tight = True)
plt.legend(loc = 'lower right')
plt.ylabel('Mean score')
plt.xlabel('Number of features')

# plot feature rankings

f4 = plt.figure(figsize = (16, 4))
ax = sns.boxplot(x = 'feature', y = 'ranking', data = feature_boxplot, order = top_features_median['feature'],
                 whis = 1.5, palette = 'Blues', fliersize = 2, notch = True)
#ax = sns.swarmplot(x = 'feature', y = 'ranking', data = feature_boxplot, order = feature_order, 
#                   size = 2, color = '.3', linewidth = 0)
ax.set_xticklabels(ax.get_xticklabels(), rotation = 90)
plt.ylabel('Ranking')
plt.xlabel('Feature')

f5 = plt.figure(figsize = (22, 4))
ax = sns.heatmap(heatmap_rankings_mean, cmap = 'Blues', linewidths = 0.5, annot = True, fmt = '.1f',
                 cbar_kws = {'ticks': [0, 19, 38], 'pad': 0.01})
#ax.set_aspect(1)
plt.ylabel('Feature selection method')
plt.xlabel('Feature')

f6 = plt.figure(figsize = (18, 4))
ax = sns.heatmap(heatmap_rankings_median, cmap = 'Blues', linewidths = 0.5, annot = True, fmt = '.0f',
                 cbar_kws = {'ticks': [0, 19, 38], 'pad': 0.01})
#ax.set_aspect(1)
plt.ylabel('Feature selection method')
plt.xlabel('Feature')

# plot parameter distributions

f7 = plt.figure()
ax = clf_results.C.value_counts().plot(kind = 'bar')
plt.ylabel('Count')
plt.xlabel('C')

f8 = plt.figure()
ax = clf_results.gamma.value_counts().plot(kind = 'bar')
plt.ylabel('Count')
plt.xlabel('Gamma')

# plot correlations

f9 = plt.figure(figsize = (4, 4))
ax = sns.heatmap(feature_corr, mask = feature_corr_mask, cmap = cmap, vmin = -1, vmax = 1, center = 0,
                 square = True, linewidths = 0.5, cbar_kws = {'shrink': 0.6, 'ticks': [-1, 0, 1],
                                                              'pad': 0})

f10 = plt.figure(figsize = (6, 6))
ax = sns.heatmap(method_corr, mask = method_corr_mask, cmap = cmap, vmin = -1, vmax = 1, center = 0,
                 square = True, linewidths = 0.5, cbar_kws = {'shrink': 0.5, 'ticks': [-1, 0, 1],
                                                              'pad': -0.1})

#%% save figures and variables

model_dir = 'Feature selection\\%s_NF%d_NM%d_NI%d' % (timestr, max(n_features), len(methods), n_iterations)

if not os.path.exists(model_dir):
    os.makedirs(model_dir)
    
for filetype in ['pdf', 'png', 'eps']:
    
    f1.savefig(model_dir + '\\' + 'heatmap_vscore_mean.' + filetype, dpi = 600, format = filetype,
               bbox_inches = 'tight', pad_inches = 0)
    f2.savefig(model_dir + '\\' + 'heatmap_tscore_mean.' + filetype, dpi = 600, format = filetype,
               bbox_inches = 'tight', pad_inches = 0)
    f3.savefig(model_dir + '\\' + 'lineplot_scores.' + filetype, dpi = 600, format = filetype,
               bbox_inches = 'tight', pad_inches = 0)
    f4.savefig(model_dir + '\\' + 'boxplot_feature_rankings.' + filetype, dpi = 600, format = filetype,
               bbox_inches = 'tight', pad_inches = 0)
    f5.savefig(model_dir + '\\' + 'heatmap_rankings_mean.' + filetype, dpi = 600, format = filetype,
               bbox_inches = 'tight', pad_inches = 0)
    f6.savefig(model_dir + '\\' + 'heatmap_rankings_median.' + filetype, dpi = 600, format = filetype,
               bbox_inches = 'tight', pad_inches = 0)
    f7.savefig(model_dir + '\\' + 'parameter_c.' + filetype, dpi = 600, format = filetype,
               bbox_inches = 'tight', pad_inches = 0)
    f8.savefig(model_dir + '\\' + 'parameter_gamma.' + filetype, dpi = 600, format = filetype,
               bbox_inches = 'tight', pad_inches = 0)
    f9.savefig(model_dir + '\\' + 'feature_corr.' + filetype, dpi = 600, format = filetype,
               bbox_inches = 'tight', pad_inches = 0)
    f10.savefig(model_dir + '\\' + 'method_corr.' + filetype, dpi = 600, format = filetype,
                bbox_inches = 'tight', pad_inches = 0)

variables_to_save = {'nan_percent': nan_percent,
                     'grid_param': grid_param,
                     'impute_labels': impute_labels,
                     'max_iter': max_iter,
                     'class_weight': class_weight,
                     'k': k,
                     'cv': cv,
                     'scoring': scoring,
                     'n_features': n_features,
                     'n_iterations': n_iterations,
                     'methods': methods,
                     'clf_results': clf_results,
                     'clf_summary': clf_summary,
                     'top_results': top_results,
                     'top_summary': top_summary,
                     'feature_corr': feature_corr,
                     'feature_corr_mask': feature_corr_mask,
                     'method_corr': method_corr,
                     'method_corr_mask': method_corr_mask,
                     'feature_rankings': feature_rankings,
                     'feature_boxplot': feature_boxplot,
                     'top_features_mean': top_features_mean,
                     'top_features_median': top_features_median,
                     'heatmap_rankings_mean': heatmap_rankings_mean,
                     'heatmap_rankings_median': heatmap_rankings_median,
                     'heatmap_vscore_mean': heatmap_vscore_mean,
                     'heatmap_tscore_mean': heatmap_tscore_mean,
                     'start_time': start_time,
                     'end_time': end_time,
                     'NPV_bins': NPV_bins,
                     'split_ratio': split_ratio,
                     'timestr': timestr,
                     'scaling_type': scaling_type,
                     'model_dir': model_dir,
                     'dataframe': dataframe,
                     'feature_labels': feature_labels,
                     'target_label': target_label}
    
save_load_variables(model_dir, variables_to_save, 'variables', 'save')
