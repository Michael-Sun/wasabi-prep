#!/usr/bin/env python
# encoding: utf-8
"""
if pain run, 
1) binarize trigger_heat TTL channel
1-1) check if it can binarize
ERROR: if cannot (primarily due to pain channels being)

2) keep empty dataframe. we'll fill this up with event boundaries and assign TTLs
"""

import os
from os.path import join
import numpy as np
from pathlib import Path
import re, logging
# from . import get_logger, set_logger_level
def _ttl_extraction(physio_df, dict_beforettl, dict_afterttl, dict_stimuli, samplingrate, metadata_df):
    """
    Parameters
    ----------
    physio_df: pandas dataframe
        acquisition file (run-wise)
    dict_beforettl: dict
        refers to event that happens before the ttl - a dictionary that contains "start" "stop" keys, 
        created via utils.preprocess._identify_boundary
    dict_afterttl: dict
        refers to event that happens after the ttl - a dictionary that contains "start" "stop" keys, 
        created via utils.preprocess._identify_boundary
    dict_stimuli: dict
        refers to event when TTL stimulus was supposed to be delivered - a dictionary that contains "start" "stop" keys, 
        created via utils.preprocess._identify_boundary
    samplingrate: int 
        sampling rate of the physiological signal
    metadata_df: pandas dataframe
        subset of behavioral data with the parameters necessary for sub/ses/run/condition information

    Returns
    -------
    metadata_df: pandas dataframe
        excludes trials where the 2nd TTL was not delivered (i.e. where trials did not reach intended temperature) 
    plateau_start: TODO: identify data type
    """
    import pandas as pd
    import itertools
    import numpy as np
    import utils
    import logging
    logger = logging.getLogger("physio.ttl")
    final_df = pd.DataFrame()
    # binarize TTL channels (raise error if channel has no TTL, despite being a pain run)
    # try:
    utils.preprocess._binarize_channel(
        physio_df,
        source_col='trigger_heat',
        new_col='ttl',
        threshold=None,
        binary_high=5,
        binary_low=0)
    # except:
    #     logger.error(
    #         f"this pain run doesn't have any TTLs {sub} {ses} {run}")


    dict_ttl = utils.preprocess._identify_boundary(physio_df, 'ttl')
    """
    Because of the sampling rate (2000hz), we get a rather long signal of the TTL, which lasts for 0.1 sec
    In order to get the correct onset time, we're going to get the mid point of this TTL square function:
    """
    ttl_onsets = list(  np.array(dict_ttl['start']) + (np.array(dict_ttl['stop']) - np.array(dict_ttl['start'])) / 2)
    logger.info(
        f"ttl onsets: {ttl_onsets}, length of ttl onset is : {len(ttl_onsets)}"
    )

    # create onset dataframe template ______________________________________________________________
    df_onset = pd.DataFrame({
        'beforettl_start': dict_beforettl['start'],
        'afterttl_end': dict_afterttl['stop'],
        'stim_start': np.nan,
        'stim_end': np.nan
    })

    df_stim = pd.DataFrame({
        'stim_start': dict_stimuli['start'],
        'stim_end': dict_stimuli['stop']
    })
    for i in range(len(df_stim)):
        idx = pd.IntervalIndex.from_arrays(df_onset['beforettl_start'],
                                            df_onset['afterttl_end'])
        start_val = df_stim.iloc[i][df_stim.columns.get_loc('stim_start')]
        interval_idx = df_onset[idx.contains(start_val)].index[0]
        df_onset.iloc[interval_idx,
                        df_onset.columns.get_loc('stim_start')] = start_val

        end_val = df_stim.iloc[i][df_stim.columns.get_loc('stim_end')]
        interval_idx = df_onset[idx.contains(end_val)].index[0]
        df_onset.iloc[interval_idx,
                        df_onset.columns.get_loc('stim_end')] = end_val
        logger.info(
            f"this is the {i}-th iteration. stim value is {start_val}, and is in between index {interval_idx}"
        )

    # define empty TTL data frame
    df_ttl = pd.DataFrame(np.nan,
                            index=np.arange(len(df_onset)),
                            columns=['ttl_1', 'ttl_2', 'ttl_3', 'ttl_4'])

    # identify which set of TTLs fall between expect and actual
    pad = 1  # seconds. you may increase the value to have a bigger event search interval
    df_onset['beforettl_start_interval'] = df_onset['beforettl_start'] - pad*samplingrate
    df_onset['afterttl_end_interval'] = df_onset['afterttl_end'] + pad*samplingrate
    idx = pd.IntervalIndex.from_arrays(df_onset['beforettl_start_interval'],
                                        df_onset['afterttl_end_interval'])

    for i in range(len(ttl_onsets)):
        iterlogger = logging.getLogger("ttl.assign_onset")
        val = ttl_onsets[i]
        iterlogger.info(f"{i}-th value: {val}")
        empty_cols = []
        try:
            interval_idx = df_onset[idx.contains(val)].index
            if len(interval_idx) == 0:
                trim = val - samplingrate * 2
                interval_idx = df_onset[idx.contains(trim)].index
                iterlogger.info(
                    f"this TTL does not belong to any event boundary")
                    
            interval_idx = interval_idx[0]
            iterlogger.info(f"\t\t* interval index: {interval_idx}")
        except:
            iterlogger.error(
                f"this TTL does not belong to any event boundary")
            continue
        mask = df_ttl.loc[[interval_idx]].isnull()
        empty_cols = list(
            itertools.compress(np.array(df_ttl.columns.to_list()),
                                mask.values[0]))
        iterlogger.info(f"\t\t* empty columns: {empty_cols}")
        df_ttl.loc[df_ttl.index[interval_idx], str(empty_cols[0])] = val
        iterlogger.info(
            f"\t\t* this is the row where the value -- {val} -- falls. on the {interval_idx}-th row"
        )

    # merge :: merge df_onset and df_ttl -> final output: final df
    final_df = pd.merge(df_onset,
                        df_ttl,
                        left_index=True,
                        right_index=True)
    final_df['ttl_r1'] = final_df['ttl_1'] - final_df['stim_start']
    final_df['ttl_r2'] = final_df['ttl_2'] - final_df['stim_start']
    final_df['ttl_r3'] = final_df['ttl_3'] - final_df['stim_start']
    final_df['ttl_r4'] = final_df['ttl_4'] - final_df['stim_start']

    ttl2 = final_df['ttl_2'].values.tolist()
    plateau_start = np.ceil(ttl2).astype(pd.Int64Dtype)
    # TODO: before we merge the data, we have to figure out a way to remove the nans
    # [x] identify row with nan in ttl2 column
    # [x] for plateau remove items with that index
    any_nans = np.argwhere(np.isnan(ttl2)).tolist()
    # if len(any_nans) != 0:
    flat_nans = [item for sublist in any_nans for item in sublist]
    for ind in flat_nans:
        plateau_start = np.delete(plateau_start, ind)
    metadata_df.drop(flat_nans, axis=0, inplace=True)
    metadata_df['trial_num'] = metadata_df.index + 1

    return metadata_df, plateau_start