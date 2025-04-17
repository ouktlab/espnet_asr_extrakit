import math
import torch
from types import SimpleNamespace
from huggingface_hub import PyTorchModelHubMixin

class PositionalEncoding(torch.nn.Module):
    def __init__(self, d_model, dropout=0.1, max_len=5000):
        super().__init__()
        self.dropout = torch.nn.Dropout(p=dropout)
        
        position = torch.arange(max_len).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2) * (-math.log(10000.0) / d_model))
        pe = torch.zeros(max_len, 1, d_model)
        pe[:, 0, 0::2] = torch.sin(position * div_term)
        pe[:, 0, 1::2] = torch.cos(position * div_term)
        pe = pe.permute(1,0,2)
        
        self.register_buffer('pe', pe)
    
    def forward(self, x):
        x = x + self.pe[:,:x.size(1),:]
        return self.dropout(x)

class PseudoCFilterbankPow(torch.nn.Module):
    """
    The matrix W should be W = [R, I; I, R] for the actual complex-valued matrix. 
    The implementation of this module is more rough, and there is no true "complex-valued" process. 
    """
    def __init__(self, input_dim, output_dim, eps=1.0e-16):
        super(PseudoCFilterbankPow, self).__init__()
        self.eps = eps
        self.bank = torch.nn.Linear(input_dim, output_dim * 2)
        torch.nn.init.xavier_normal_(self.bank.weight)
        self.pow = torch.nn.Parameter(torch.ones(output_dim) * 1.0e-1)

    def forward(self, inputs, **kwargs):
        """ inputs: [B, F, D]
        """
        inputs = self.bank(inputs)
        inputs = torch.complex(inputs[:,:,0::2], inputs[:,:,1::2])
        return torch.pow(torch.abs(inputs)+self.eps, torch.abs(self.pow))
    
class TransformerSpeechSpecEnhancer(torch.nn.Module, PyTorchModelHubMixin):
    """ speech enhancer in the amplitude spectrogram domain.
        based on the structure of our Interspeech2023 (MD-ASR) and APSIPA2024 (VAD) papers. 
    """
    def __init__(self, n_fbin=256, n_fbank=256, n_fwd=31, n_bwd=32, n_decimate=2,
                 tf_dims=1024, tf_nhead=8, tf_num_layers=1, n_clsdim=8192):
        super(TransformerSpeechSpecEnhancer, self).__init__()
        
        #
        self.n_fbin = n_fbin
        self.n_fbank = n_fbank
        self.n_fwd = n_fwd
        self.n_bwd = n_bwd
        self.n_frame = (1 + n_fwd + n_bwd)
        self.n_clsdim = n_clsdim
        
        self.n_decimate = n_decimate
        self.n_half = math.ceil(self.n_frame / self.n_decimate)
        self.n_quarter = math.ceil(self.n_half / self.n_decimate)
        
        #
        self.fbank =  PseudoCFilterbankPow(self.n_fbin, self.n_fbank)
        self.norm = torch.nn.LayerNorm(self.n_fbank)
        self.posenc = PositionalEncoding(self.n_fbank)

        #
        enclayer_full = torch.nn.TransformerEncoderLayer(self.n_fbank, dim_feedforward=tf_dims, nhead=tf_nhead, batch_first=True)
        self.transformer_full = torch.nn.TransformerEncoder(enclayer_full, num_layers=1)
    
        enclayer_half = torch.nn.TransformerEncoderLayer(self.n_fbank, dim_feedforward=tf_dims, nhead=tf_nhead, batch_first=True)
        self.transformer_half = torch.nn.TransformerEncoder(enclayer_half, num_layers=1)
        
        enclayer_quarter = torch.nn.TransformerEncoderLayer(self.n_fbank, dim_feedforward=tf_dims, nhead=tf_nhead, batch_first=True)
        self.transformer_quarter = torch.nn.TransformerEncoder(enclayer_quarter, num_layers=tf_num_layers)
        
        self.linear1 = torch.nn.Linear(self.n_fbank * self.n_quarter, self.n_clsdim)
        self.linear2 = torch.nn.Linear(self.n_clsdim, self.n_fbin)
        self.relu = torch.nn.LeakyReLU()
    
    def splice(self, feat):
        [nframe, nch, nfreq] = feat.shape        
        #
        ncat = 1 + self.n_fwd + self.n_bwd
        newfeat = torch.zeros((nframe, ncat, nfreq)).to(feat.device)
        
        # padding
        newfeat[:self.n_bwd,:,:] = feat[0,0,:]
        newfeat[-self.n_fwd:,:,:] = feat[-1,0,:]
        
        # naive frame-by-frame concatenation :P
        for t in range(nframe):
            s_pos = t - self.n_bwd
            s_dif = 0
            if s_pos <= 0:
                s_dif = abs(s_pos)
                s_pos = 0            
            e_pos = t + self.n_fwd + 1
            e_dif = ncat
            if e_pos >= nframe:
                e_dif = ncat - (e_pos - nframe)
                e_pos = nframe
                
            newfeat[t,s_dif:e_dif,:] = feat[s_pos:e_pos,0,:]
        
        return newfeat
            
    
    def forward(self, inputs, labels=None):
        """
        inputs: amplitude (absolute) spectrogram
        """

        # [Batch, Channel, Frame, FreqBin]: spectrogram-wise prediction. mainly used for prediction.
        if len(inputs.shape) == 4:
            [B, C, F, D] = inputs.shape
            if B != 1:
                print("[CAUTION]: only 1st-batch data is used")
            #if C != 1:
            #    print("[CAUTION]: only 1st-channel data is used")
            predicts = self.splice(inputs[0,:,:,:].permute(1,0,2))
            predicts = self.forward(predicts[:,:,1:], labels)
            if labels is not None:
                return preditcs
            predicts = predicts.permute(1,0,2).unsqueeze(0)
            predicts = torch.cat([inputs[:,:,:,0:1], predicts], dim=3)
            return predicts
        
        # [Batch, SpliceFrame, FreqBin]: block-wise prediction. mainly used for training. 
        elif len(inputs.shape) == 3:            
            [B, F, D] = inputs.shape
            
            # blockwise scale-normalization
            scales = torch.mean(inputs, dim=(1,2)).reshape(B,1,1)
            predicts = inputs / (scales + 1.0e-10)
            
            # discrimination            
            predicts = self.fbank(predicts)
            predicts = self.norm(predicts)
            predicts = self.posenc(predicts)

            predicts = self.transformer_full(predicts)
            predicts = self.transformer_half(predicts[:,0::self.n_decimate,:])
            predicts = self.transformer_quarter(predicts[:,0::self.n_decimate,:])
            
            predicts = self.linear1(predicts.reshape(B, self.n_quarter * self.n_fbank))
            predicts = torch.cat([torch.sigmoid(predicts[:,0::2]), self.relu(predicts[:,1::2])], dim=1)
            predicts = self.linear2(predicts)
            predicts = torch.sigmoid(predicts)
            
            # predicts[B, 1, D]
            predicts = (predicts * inputs[:,self.n_bwd,:]).unsqueeze(1)

            #####
            if labels is not None:
                loss = self.loss(predicts, labels, inputs[:,self.n_bwd,:].unsqueeze(1))
                return SimpleNamespace(**{
                    'loss': loss,
                })

            return predicts

        return None

    def loss(self, predicts, labels, inputs, eps=1.0e-8):
        """ based on the spectrogram-domain loss. feature-domain loss is not used in this simple example. 
        """
        #
        B, F, D = predicts.shape

        # 
        mask_err = labels > inputs
        residual = (labels - inputs) * mask_err
        
        log_err = torch.log(labels+eps) - torch.log(residual+predicts+eps)
        loss = torch.sum(torch.abs(log_err)) / (B * F * D)
        return loss

#####
# v2
class MixedFilterbank(torch.nn.Module):
    def __init__(self, input_dim, output_dim, eps=1.0e-16):
        super(MixedFilterbank, self).__init__()
        output_dim_h = int(output_dim/2)
        self.eps = eps
    
        # linear-complexabs-pow
        self.bank_c = torch.nn.Linear(input_dim, output_dim)
        torch.nn.init.xavier_normal_(self.bank_c.weight)
        self.pow = torch.nn.Parameter(torch.ones(output_dim_h) * 1.0e-1)
        
        # log-linear
        self.bank_r = torch.nn.Linear(input_dim, output_dim_h)
        torch.nn.init.xavier_normal_(self.bank_r.weight)
        
        
    def forward(self, inputs, **kwargs):
        fbank_c = self.bank_c(inputs)
        fbank_c = torch.complex(fbank_c[:,:,0::2], fbank_c[:,:,1::2])
        fbank_c = torch.pow(torch.abs(fbank_c)+self.eps, torch.abs(self.pow))
        
        fbank_r = self.bank_r(torch.log(torch.abs(inputs)+self.eps))
        return torch.cat([fbank_c, fbank_r], dim=2)


# X: [B, C, F]
class TransformerSpeechSpecEnhancerV2(torch.nn.Module, PyTorchModelHubMixin):
    def __init__(self, n_fbin=256, n_fbank=256, n_fwd=31, n_bwd=32, n_decimate=2,
                 tf_dims=1024, tf_nhead=8, tf_num_layers=1, n_clsdim=8192):
        super(TransformerSpeechSpecEnhancerV2, self).__init__()
        
        #
        self.n_fbin = n_fbin
        self.n_fbank = n_fbank
        self.n_fwd = n_fwd
        self.n_bwd = n_bwd
        self.n_frame = (1 + n_fwd + n_bwd)
        
        self.n_decimate = n_decimate
        self.n_half = math.ceil(self.n_frame / self.n_decimate)
        self.n_quarter = math.ceil(self.n_half / self.n_decimate)
        self.n_clsdim = n_clsdim
        
        #
        self.mfbank = MixedFilterbank(self.n_fbin, self.n_fbank)
        self.norm = torch.nn.LayerNorm(self.n_fbank)
        self.posenc = PositionalEncoding(self.n_fbank)
        
        #
        enclayer_full = torch.nn.TransformerEncoderLayer(self.n_fbank, dim_feedforward=tf_dims, nhead=tf_nhead, batch_first=True)
        self.transformer_full = torch.nn.TransformerEncoder(enclayer_full, num_layers=1)
        
        enclayer_half = torch.nn.TransformerEncoderLayer(self.n_fbank, dim_feedforward=tf_dims, nhead=tf_nhead, batch_first=True)
        self.transformer_half = torch.nn.TransformerEncoder(enclayer_half, num_layers=1)
        
        enclayer_quarter = torch.nn.TransformerEncoderLayer(self.n_fbank, dim_feedforward=tf_dims, nhead=tf_nhead, batch_first=True)
        self.transformer_quarter = torch.nn.TransformerEncoder(enclayer_quarter, num_layers=tf_num_layers)
        
        self.linear1 = torch.nn.Linear(self.n_fbank * self.n_quarter, self.n_clsdim)
        self.linear2 = torch.nn.Linear(self.n_clsdim, self.n_fbin)
        self.relu = torch.nn.LeakyReLU()
        
        
    def splice(self, feat):
        [nframe, nch, nfreq] = feat.shape
        
        #
        ncat = 1 + self.n_fwd + self.n_bwd
        newfeat = torch.zeros((nframe, ncat, nfreq)).to(feat.device)
        
        # padding
        newfeat[:self.n_bwd,:,:] = feat[0,0,:]
        newfeat[-self.n_fwd:,:,:] = feat[-1,0,:]
        
        #
        for t in range(nframe):
            s_pos = t - self.n_bwd
            s_dif = 0
            if s_pos <= 0:
                s_dif = abs(s_pos)
                s_pos = 0
            
            e_pos = t + self.n_fwd + 1
            e_dif = ncat
            if e_pos >= nframe:
                e_dif = ncat - (e_pos - nframe)
                e_pos = nframe
                
            newfeat[t,s_dif:e_dif,:] = feat[s_pos:e_pos,0,:]
            
        return newfeat

    
    def forward(self, inputs, labels=None):
        """
        inputs: absolute spectrogram
        """
        
        # [Batch, Channel, Frame, FreqBin]: spectrogram-wise prediction
        if len(inputs.shape) == 4:
            [B, C, F, D] = inputs.shape
            if B != 1:
                print("[CAUTION]: only 1st-batch data is used")
            if C != 1:
                print("[CAUTION]: only 1st-channel data is used")
            predicts = self.splice(inputs[0,:,:,:].permute(1,0,2))
            predicts = self.forward(predicts[:,:,1:], labels)
            if labels is not None:
                return preditcs
            predicts = predicts.permute(1,0,2).unsqueeze(0)
            predicts = torch.cat([inputs[:,:,:,0:1], predicts], dim=3)
            return predicts

        # [Batch, SpliceFrame, FreqBin]: block-wise prediction
        elif len(inputs.shape) == 3:
            [B, F, D] = inputs.shape
            
            # blockwise scale-normalization
            scales = torch.mean(inputs, dim=(1,2)).reshape(B,1,1)
            predicts = inputs / (scales + 1.0e-10)
            
            # discrimination
            predicts = self.mfbank(predicts)
            predicts = self.norm(predicts)
            predicts = self.posenc(predicts)
            
            predicts = self.transformer_full(predicts)
            predicts = self.transformer_half(predicts[:,0::self.n_decimate,:])
            predicts = self.transformer_quarter(predicts[:,0::self.n_decimate,:])
            
            predicts = self.linear1(predicts.reshape(B, self.n_quarter * self.n_fbank))
            predicts = torch.cat([torch.sigmoid(predicts[:,0::2]), self.relu(predicts[:,1::2])], dim=1)
            predicts = self.linear2(predicts)
            predicts = torch.sigmoid(predicts)
            
            # predicts[B, 1, D]
            predicts = (predicts * inputs[:,self.n_bwd,:]).unsqueeze(1)
            
            #####
            if labels is not None:
                loss = self.loss(predicts, labels, inputs[:,self.n_bwd,:].unsqueeze(1))
                return SimpleNamespace(**{
                    'loss': loss,
                })
            
            return predicts
        
        return None

    '''
    head: B, n_label
    labels: B, n_label
    '''
    def loss(self, predicts, labels, inputs):
        #
        B, F, D = predicts.shape
        eps = 1.0e-8
        
        # for log power spectrum domain
        mask_err = labels > inputs
        residual = (labels - inputs) * mask_err
        
        log_err = torch.log(labels+eps) - torch.log(residual+predicts+eps)
        loss = torch.sum(torch.abs(log_err)) / (B * F * D)
        return loss


##### 
#
def main():
    import argparse
    import matplotlib.pyplot as plt
    parser = argparse.ArgumentParser()
    parser.add_argument('wavfile', type=str)
    parser.add_argument('--parampath', type=str, default='ouktlab/TSSE-v1_csjcore-cln_pse-cln')
    parser.add_argument('--model', type=str, default='v1', help='model version: v1, v2.  default [v1]')
    parser.add_argument('--nthread', type=int, default=2)
    args = parser.parse_args()

    ###
    torch.set_num_threads(args.nthread)
    
    ###
    if args.model == 'v1':
        model = TransformerSpeechSpecEnhancer.from_pretrained(args.parampath)
    elif args.model == 'v2':
        model = TransformerSpeechSpecEnhancerV2.from_pretrained(args.parampath)
    else:
        print('[ERROR]: invalid "--model" parameter')
        quit()
    
    model.eval()

    import torchaudio
    s, fs = torchaudio.load(args.wavfile)
    window = torch.hann_window(512, dtype=s.dtype, device='cpu')

    ###
    import time
    time_beg = time.perf_counter()
    wave_time = len(s.T)/fs
    ##
    spec = torch.stft(s, n_fft=512, hop_length=128, window=window, 
                      win_length=512, center=False, onesided=True, return_complex=True)
    spec = torch.abs(spec).unsqueeze(0).permute(0,1,3,2)
    
    ##
    with torch.no_grad():
        pred = model(spec)

    ##
    proc_time = time.perf_counter() - time_beg
    print(f'[LOG]: RTF on CPU ({args.nthread}-threads): {proc_time/wave_time:.3f} ({proc_time:.2f}/{wave_time:.2f})')
    
    ###
    fig = plt.figure()
    plt.imshow(torch.log(spec.squeeze().T), origin="lower", aspect="auto", cmap="jet")
    plt.colorbar()
    plt.clim([-15, 5])
    
    fig = plt.figure()
    plt.imshow(torch.log(pred.detach().squeeze().T), origin="lower", aspect="auto", cmap="jet")
    plt.colorbar()
    plt.clim([-15, 5])
    
    plt.show()


if __name__ == '__main__':
    main()
