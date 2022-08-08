import json
import logging
import os
import torch
from torchvision import transforms
from torchvision import models
import torch.nn as nn
import pandas as pd

# build a GRU model
class GRUModel(nn.Module):
    def __init__(self, input_size, output_size, hidden_dim, n_layers):
        super(GRUModel, self).__init__()

        self.hidden_dim = hidden_dim
        self.n_layers = n_layers

        self.gru = nn.GRU(input_size, hidden_dim, n_layers, batch_first=True, dropout=0.2)
        self.fc = nn.Linear(hidden_dim, output_size).float()
        self.relu = nn.ReLU()
        
    def forward(self, x):
        out, h = self.gru(x)
        out = self.fc(self.relu(out))
        return out, h
    
    def init_hidden(self, batch_size):
        weight = next(self.parameters()).data
        hidden = weight.new(self.n_layers, batch_size, self.hidden_dim).zero_()
        return hidden

def model_fn(model_dir, model):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info('Loading the model.') 
    model = GRUModel(2548, 3, 128, 2)
    with open('model.pth', 'rb') as f:
        model.load_state_dict(torch.load(f))
    model.to(device).eval()
    logger.info('Done loading model')
    return model

def input_fn(request_body, content_type='application/json'):
    logger.info('Deserializing the input data.')
    if content_type == 'application/json':
        input_data = json.loads(request_body)
        features = input_data['features']
        #features = json.loads(message)
        input_features = pd.Series(features).to_numpy()
    raise Exception(f'Requested unsupported ContentType in content_type {content_type}')
    
def predict_fn(input_data, model):
    logger.info('Generating prediction based on input parameters.')
    if torch.cuda.is_available():
        input_data = input_data.view(1, 1, 2548).cuda()
    else:
        input_data = input_data.view(1, 1, 2548)
    with torch.no_grad():
        model.eval()
        out = model(input_data)
        ps = torch.exp(out)
    return ps

def output_fn(prediction_output, accept='application/json'):
    logger.info('Serializing the generated output.')
    label_dict= {0:'STRESSED', 1:'CALM', 2:'GOOD-MOOD'}
    
    topk, topclass = prediction_output.topk(3, dim=1)
    result = []
    
    for i in range(3):
        pred = {'prediction': classes[topclass.cpu().numpy()[0][i]], 'score': f'{topk.cpu().numpy()[0][i] * 100}%'}
        logger.info(f'Adding pediction: {pred}')
        result.append(pred)
​
    if accept == 'application/json':
        return json.dumps(result), accept
    raise Exception(f'Requested unsupported ContentType in Accept:{accept}')