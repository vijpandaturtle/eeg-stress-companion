from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from AWSIoTPythonSDK.exception.AWSIoTExceptions import publishTimeoutException
from AWSIoTPythonSDK.core.protocol.internal.defaults import DEFAULT_OPERATION_TIMEOUT_SEC

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

def streamEEGData(timeout, deviceId):
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
    message = {}
    for feat_vector in features:
        feat_vector = pd.Series(feat_vector)
        ts = time.time()
        message['deviceid'] = deviceId
        message['timestamp'] = ts
        message['features'] = feat_vector.to_json()
        messageJson = json.dumps(message)
        myAWSIoTMQTTClient.publish(topic, messageJson, 1)
        time.sleep(10)        
    board.stop_stream()
    board.release_session()
    
# Auth certificate paths
host = 'a1yosmnxnz1zrc-ats.iot.us-east-1.amazonaws.com'
rootCAPath = './certificates/AmazonRootCA1.pem'
certificatePath = './certificates/7713b3723dcb191b9c85094e9ad0ff32b88f866301d3ff1cafcecd1bd0fd0c5a-certificate.pem.crt'
privateKeyPath = './certificates/7713b3723dcb191b9c85094e9ad0ff32b88f866301d3ff1cafcecd1bd0fd0c5a-private.pem.key'

# Parameters
port = 443
useWebsocket = False
clientId = 'client001'
topic = 'iot/eeg'
deviceId = 'Ganglion101'

# Port defaults
if useWebsocket and port:  # When no port override for WebSocket, default to 443
    port = 443
if useWebsocket and not port:  # When no port override for non-WebSocket, default to 8883
    port = 8883

# Configure logging
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

# Init AWSIoTMQTTClient
myAWSIoTMQTTClient = None
if useWebsocket:
    myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId, useWebsocket=True)
    myAWSIoTMQTTClient.configureEndpoint(host, port)
    myAWSIoTMQTTClient.configureCredentials(rootCAPath)
else:
    myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
    myAWSIoTMQTTClient.configureEndpoint(host, port)
    myAWSIoTMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# Connect and subscribe to AWS IoT
myAWSIoTMQTTClient.connect()
streamEEGData(60, deviceId)
time.sleep(90)
print("Intiate the connection closing process from AWS.")
myAWSIoTMQTTClient.disconnect()
print("Connection closed.")
