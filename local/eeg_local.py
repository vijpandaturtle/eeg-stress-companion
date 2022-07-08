import brainflow
from brainflow.board_shim import BoardShim, BrainFlowInputParams, LogLevels, BoardIds
from brainflow.data_filter import DataFilter, FilterTypes, AggOperations

import logging
import datetime
import argparse
import json
import random
import csv
import time
import sched
import pandas as pd
import numpy as np

from eeg_feature_gen.EEG_generate_training_matrix import gen_training_matrix

def streamEEGData(timeout):
    #Creating an empty publish message
    BoardShim.enable_dev_board_logger()
    #Board id for ganglion 
    board_id = 1 
    #Setting serial port for the board
    params = BrainFlowInputParams()
    params.serial_port = 'COM6'
    
    board = BoardShim(board_id, params)
    eeg_channels = BoardShim.get_eeg_channels(board_id)
    sampling_rate = BoardShim.get_sampling_rate(board_id)
    timestamp = BoardShim.get_timestamp_channel(board_id)
    board.prepare_session()
    board.start_stream()
    final_eeg_df = pd.DataFrame()
    final_timestamp_df = pd.DataFrame()
    keepAlive = 0

    while keepAlive < timeout:
        #get board data removes data from the buffer
        #while board.get_board_data_count()<250:
        #    time.sleep(1)
        data = board.get_board_data()
        #creating a dataframe of the eeg data to extract eeg values later
        eegdf = pd.DataFrame(np.transpose(data[eeg_channels]))
        eegdf_col_names = ["TP9", "AF7", "AF8", "TP10"]
        eegdf.columns = eegdf_col_names
        timedf = pd.DataFrame(np.transpose(data[timestamp]))
        final_eeg_df = pd.concat([final_eeg_df, eegdf])
        final_timestamp_df = pd.concat([final_timestamp_df, timedf])
        time.sleep(1)
        keepAlive += 1
    final_eeg_df['timestamp'] = final_timestamp_df
    final_eeg_df['noise'] = np.zeros((len(final_eeg_df),1))
    final_eeg_df = final_eeg_df[["timestamp", "TP9", "AF7", "AF8", "TP10", "noise"]]
    final_eeg_df.to_csv('out.csv',index=False)
    features = gen_training_matrix('out.csv',cols_to_ignore = -1)
    board.stop_stream()
    board.release_session()
    return features
    
#streamEEGData(60, deviceId)
