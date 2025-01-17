import torch
from torch import nn, optim
import torch.nn.functional as F
import torch.nn as nn 
from torch import nn, Tensor
import torch.utils.data as data_utils
import random
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class GRUEncoder_Att(nn.Module):
    def __init__(self, hidden_dim, layer_dim, lags, horizons, n_features):
        super(GRUEncoder_Att, self).__init__()
        self.hidden_dim = hidden_dim
        self.layer_dim = layer_dim
        self.gru = nn.GRU(n_features, hidden_dim, layer_dim, batch_first=True)

    def forward(self, x):
        out, hidden = self.gru(x)
        return out, hidden
    
class GRUDecoder_Att(nn.Module):
    def __init__(self, hidden_dim, layer_dim, lags, horizons, n_features):
        super(GRUDecoder_Att, self).__init__()
        self.layer_dim = layer_dim
        self.hidden_dim = hidden_dim
        self.linear_encoder = nn.Linear(hidden_dim, hidden_dim)
        self.linear_decoder = nn.Linear(hidden_dim, hidden_dim)
        self.embed = nn.Linear(n_features, hidden_dim)
        self.attn = nn.Linear(self.hidden_dim*2, hidden_dim)
        self.v = nn.Linear(hidden_dim, 1, bias = False)        
        self.gru = nn.GRU(hidden_dim, hidden_dim, layer_dim, batch_first=True)
        self.fc1 = nn.Linear(hidden_dim, 1)
        self.fc4 = nn.Linear(hidden_dim, n_features)
        self.lags = lags

    def forward(self, x, hidden, encoder_outputs, decoder_outputs): 
        seq_len = encoder_outputs.shape[1]
        decoder_repeat = decoder_outputs.repeat(1,self.lags, 1)
        encoder_outputs = self.linear_encoder(encoder_outputs)
        decoder_repeat = self.linear_decoder(decoder_repeat)
        concat = torch.cat((decoder_repeat, encoder_outputs), dim = 2)
        nonl = torch.tanh(concat)
        energy = self.attn(nonl)
        attention = self.v(energy).squeeze(2)
        attention = F.softmax(attention, dim=1)
        attention = attention.unsqueeze(1)
        attention = attention
        context_vector = torch.bmm(attention, encoder_outputs)
        x = torch.tanh(self.embed(x))
        rnn_input = context_vector + x
        output, hidden = self.gru(rnn_input, hidden)
        out = output
        out_1 = self.fc1(torch.squeeze(output))
        out_4 = self.fc4(hidden[-1])
        return out, out_1, out_4, hidden
    
class GRU_Seq2Seq_Att(nn.Module):    
    def __init__(self, configs):
        super(GRU_Seq2Seq_Att, self).__init__()
        hidden_dim = configs.d_model
        layer_dim = 1
        n_past = configs.seq_len
        n_future = configs.pred_len
        features = configs.enc_in
        lags = n_past
        horizons = n_future
        self.enc_in = configs.enc_in

        n_features = features
        self.encoder = GRUEncoder_Att(hidden_dim, layer_dim, lags, horizons, n_features)
        self.decoder = GRUDecoder_Att(hidden_dim, layer_dim, lags, horizons, n_features)
        self.lags = lags
        self.horizons = horizons
        self.n_features = n_features

    def forward(self, src, trg, x_dec, x_mark_dec,
                enc_self_mask=None, dec_self_mask=None, dec_enc_mask=None, train=False):
        output, hidden = self.encoder(src)
        outputs = torch.zeros(trg.shape[0], self.horizons, self.enc_in).to(device)
        input_trg = src[:,src.shape[1]-1:src.shape[1],:]
        start = 0
        end = 1
        if(train == True):
            out = output[:,-1,:].unsqueeze(1)
            for t in range(0, self.horizons):
                out, out_1, out_4, hidden = self.decoder(input_trg, hidden, output, out)
                outputs[:,start:end] = out_4.unsqueeze(1)
                if random.random() < 0.4:
                    input_trg = trg[:,start:end,:]
                else:
                    input_trg = out_4.unsqueeze(1)
                start = end 
                end = end + 1
        elif(train == False):
            out = output[:,-1,:].unsqueeze(1)
            for t in range(0, self.horizons):
                out, out_1, out_4, hidden = self.decoder(input_trg, hidden, output, out)
                outputs[:,start:end] = out_4.unsqueeze(1)
                input_trg = out_4.unsqueeze(1)
                start = end 
                end = end + 1
        return outputs