from copy import deepcopy
from joblib import Parallel, delayed
import multiprocessing

import numpy as np
import pandas as pd
import time
import datetime
import matplotlib as plt
import matplotlib.colors as pltcolors
import matplotlib.cm as cmx
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
# from sklearn.cross_validation import KFold
from pyFTS.partitioners import partitioner, Grid, Huarng, Entropy, FCM
from pyFTS.benchmarks import Measures, naive, arima, ResidualAnalysis, ProbabilityDistribution
from pyFTS.common import Membership, FuzzySet, FLR, Transformations, Util
from pyFTS import fts, chen, yu, ismailefendi, sadaei, hofts, hwang,  pwfts, ifts
from pyFTS.benchmarks import  benchmarks


def run_point(mfts, partitioner, train_data, test_data, transformation=None, indexer=None):
    pttr = str(partitioner.__module__).split('.')[-1]
    _key = mfts.shortname + " n = " + str(mfts.order) + " " + pttr + " q = " + str(partitioner.partitions)
    mfts.partitioner = partitioner
    if transformation is not None:
        mfts.appendTransformation(transformation)

    try:
        _start = time.time()
        mfts.train(train_data, partitioner.sets, order=mfts.order)
        _end = time.time()
        times = _end - _start

        _start = time.time()
        _rmse, _smape, _u = benchmarks.get_point_statistics(test_data, mfts, indexer)
        _end = time.time()
        times += _end - _start
    except Exception as e:
        print(e)
        _rmse = np.nan
        _smape = np.nan
        _u = np.nan
        times = np.nan

    ret = {'key': _key, 'obj': mfts, 'rmse': _rmse, 'smape': _smape, 'u': _u, 'time': times}

    print(ret)

    return ret


def point_sliding_window(data, windowsize, train=0.8, models=None, partitioners=[Grid.GridPartitioner],
                         partitions=[10], max_order=3, transformation=None, indexer=None, dump=False,
                         save=False, file=None, sintetic=False):
    _process_start = time.time()

    print("Process Start: {0: %H:%M:%S}".format(datetime.datetime.now()))

    num_cores = multiprocessing.cpu_count()

    pool = []

    objs = {}
    rmse = {}
    smape = {}
    u = {}
    times = {}

    for model in benchmarks.get_point_methods():
        mfts = model("")

        if mfts.isHighOrder:
            for order in np.arange(1, max_order + 1):
                if order >= mfts.minOrder:
                    mfts = model("")
                    mfts.order = order
                    pool.append(mfts)
        else:
            pool.append(mfts)

    experiments = 0
    for ct, train, test in Util.sliding_window(data, windowsize, train):
        experiments += 1

        if dump: print('\nWindow: {0}\n'.format(ct))

        for partition in partitions:

            for partitioner in partitioners:

                data_train_fs = partitioner(train, partition, transformation=transformation)

                results = Parallel(n_jobs=num_cores)(
                    delayed(run_point)(deepcopy(m), deepcopy(data_train_fs), deepcopy(train), deepcopy(test),
                                       transformation)
                    for m in pool)

                for tmp in results:
                    if tmp['key'] not in objs:
                        objs[tmp['key']] = tmp['obj']
                        rmse[tmp['key']] = []
                        smape[tmp['key']] = []
                        u[tmp['key']] = []
                        times[tmp['key']] = []
                    rmse[tmp['key']].append(tmp['rmse'])
                    smape[tmp['key']].append(tmp['smape'])
                    u[tmp['key']].append(tmp['u'])
                    times[tmp['key']].append(tmp['time'])

    _process_end = time.time()

    print("Process End: {0: %H:%M:%S}".format(datetime.datetime.now()))

    print("Process Duration: {0}".format(_process_end - _process_start))

    return benchmarks.save_dataframe_point(experiments, file, objs, rmse, save, sintetic, smape, times, u)


def run_interval(mfts, partitioner, train_data, test_data, transformation=None, indexer=None):
    pttr = str(partitioner.__module__).split('.')[-1]
    _key = mfts.shortname + " n = " + str(mfts.order) + " " + pttr + " q = " + str(partitioner.partitions)
    mfts.partitioner = partitioner
    if transformation is not None:
        mfts.appendTransformation(transformation)

    try:
        _start = time.time()
        mfts.train(train_data, partitioner.sets, order=mfts.order)
        _end = time.time()
        times = _end - _start

        _start = time.time()
        _sharp, _res, _cov = benchmarks.get_interval_statistics(test_data, mfts)
        _end = time.time()
        times += _end - _start
    except Exception as e:
        print(e)
        _sharp = np.nan
        _res = np.nan
        _cov = np.nan
        times = np.nan

    ret = {'key': _key, 'obj': mfts, 'sharpness': _sharp, 'resolution': _res, 'coverage': _cov, 'time': times}

    print(ret)

    return ret


def interval_sliding_window(data, windowsize, train=0.8, models=None, partitioners=[Grid.GridPartitioner],
                         partitions=[10], max_order=3, transformation=None, indexer=None, dump=False,
                         save=False, file=None, sintetic=False):
    _process_start = time.time()

    print("Process Start: {0: %H:%M:%S}".format(datetime.datetime.now()))

    num_cores = multiprocessing.cpu_count()

    pool = []

    objs = {}
    sharpness = {}
    resolution = {}
    coverage = {}
    times = {}

    for model in benchmarks.get_interval_methods():
        mfts = model("")

        if mfts.isHighOrder:
            for order in np.arange(1, max_order + 1):
                if order >= mfts.minOrder:
                    mfts = model("")
                    mfts.order = order
                    pool.append(mfts)
        else:
            pool.append(mfts)

    experiments = 0
    for ct, train, test in Util.sliding_window(data, windowsize, train):
        experiments += 1

        if dump: print('\nWindow: {0}\n'.format(ct))

        for partition in partitions:

            for partitioner in partitioners:

                data_train_fs = partitioner(train, partition, transformation=transformation)

                results = Parallel(n_jobs=num_cores)(
                    delayed(run_interval)(deepcopy(m), deepcopy(data_train_fs), deepcopy(train), deepcopy(test),
                                       transformation)
                    for m in pool)

                for tmp in results:
                    if tmp['key'] not in objs:
                        objs[tmp['key']] = tmp['obj']
                        sharpness[tmp['key']] = []
                        resolution[tmp['key']] = []
                        coverage[tmp['key']] = []
                        times[tmp['key']] = []

                    sharpness[tmp['key']].append(tmp['sharpness'])
                    resolution[tmp['key']].append(tmp['resolution'])
                    coverage[tmp['key']].append(tmp['coverage'])
                    times[tmp['key']].append(tmp['time'])

    _process_end = time.time()

    print("Process End: {0: %H:%M:%S}".format(datetime.datetime.now()))

    print("Process Duration: {0}".format(_process_end - _process_start))

    return benchmarks.save_dataframe_interval(coverage, experiments, file, objs, resolution, save, sharpness, sintetic, times)


def run_ahead(mfts, partitioner, train_data, test_data, steps, resolution, transformation=None, indexer=None):
    pttr = str(partitioner.__module__).split('.')[-1]
    _key = mfts.shortname + " n = " + str(mfts.order) + " " + pttr + " q = " + str(partitioner.partitions)
    mfts.partitioner = partitioner
    if transformation is not None:
        mfts.appendTransformation(transformation)

    try:
        _start = time.time()
        mfts.train(train_data, partitioner.sets, order=mfts.order)
        _end = time.time()
        times = _end - _start

        _crps1, _crps2, _t1, _t2 = benchmarks.get_distribution_statistics(test_data, mfts, steps=steps,
                                                              resolution=resolution)
        _t1 += times
        _t2 += times
    except Exception as e:
        print(e)
        _crps1 = np.nan
        _crps2 = np.nan
        _t1 = np.nan
        _t2 = np.nan

    ret = {'key': _key, 'obj': mfts, 'CRPS_Interval': _crps1, 'CRPS_Distribution': _crps2, 'TIME_Interval': _t1, 'TIME_Distribution': _t2}

    print(ret)

    return ret


def ahead_sliding_window(data, windowsize, train, steps,resolution, models=None, partitioners=[Grid.GridPartitioner],
                         partitions=[10], max_order=3, transformation=None, indexer=None, dump=False,
                         save=False, file=None, sintetic=False):
    _process_start = time.time()

    print("Process Start: {0: %H:%M:%S}".format(datetime.datetime.now()))

    num_cores = multiprocessing.cpu_count()

    pool = []

    objs = {}
    crps_interval = {}
    crps_distr = {}
    times1 = {}
    times2 = {}

    for model in benchmarks.get_interval_methods():
        mfts = model("")

        if mfts.isHighOrder:
            for order in np.arange(1, max_order + 1):
                if order >= mfts.minOrder:
                    mfts = model("")
                    mfts.order = order
                    pool.append(mfts)
        else:
            pool.append(mfts)

    experiments = 0
    for ct, train, test in Util.sliding_window(data, windowsize, train):
        experiments += 1

        if dump: print('\nWindow: {0}\n'.format(ct))

        for partition in partitions:

            for partitioner in partitioners:

                data_train_fs = partitioner(train, partition, transformation=transformation)

                results = Parallel(n_jobs=num_cores)(
                    delayed(run_ahead)(deepcopy(m), deepcopy(data_train_fs), deepcopy(train), deepcopy(test),
                                       steps, resolution, transformation)
                    for m in pool)

                for tmp in results:
                    if tmp['key'] not in objs:
                        objs[tmp['key']] = tmp['obj']
                        crps_interval[tmp['key']] = []
                        crps_distr[tmp['key']] = []
                        times1[tmp['key']] = []
                        times2[tmp['key']] = []

                    crps_interval[tmp['key']].append(tmp['CRPS_Interval'])
                    crps_distr[tmp['key']].append(tmp['CRPS_Distribution'])
                    times1[tmp['key']].append(tmp['TIME_Interval'])
                    times2[tmp['key']].append(tmp['TIME_Distribution'])

    _process_end = time.time()

    print("Process End: {0: %H:%M:%S}".format(datetime.datetime.now()))

    print("Process Duration: {0}".format(_process_end - _process_start))

    return benchmarks.save_dataframe_ahead(experiments, file, objs, crps_interval, crps_distr, times1, times2, save, sintetic)
