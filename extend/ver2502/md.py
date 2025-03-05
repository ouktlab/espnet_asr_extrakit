import copy
from typing import Optional, Tuple, Union

import humanfriendly
import numpy as np
import torch
import yaml
from torch_complex.tensor import ComplexTensor
from typeguard import typechecked

from espnet2.asr.frontend.abs_frontend import AbsFrontend
from espnet2.layers.log_mel import LogMel
from espnet2.layers.stft import Stft
from espnet2.utils.get_default_kwargs import get_default_kwargs
from espnet.nets.pytorch_backend.frontends.frontend import Frontend

from importlib import import_module

### samplers
class SamplerUniform:
    def __init__(self, N=8):
        self.N = N
        print('[LOG]: SamplerUniform, ', N)

    def draw(self, enh_feats, obs_feat, feats_lens):
        B, T, D = enh_feats.shape        
        input_feats = torch.zeros(B * self.N, T, D).to(obs_feat.device)
        for i in range(B):
            step_feat = obs_feat - enh_feats[i,:,:]        
            for n in range(self.N):
                w = float(n) / (self.N - 1)
                input_feats[n + self.N * i] = enh_feats[i,:,:] + w * step_feat
        feats_lens = torch.ones(self.N * B, dtype=torch.long).to(feats_lens.device) * feats_lens[0]
        return input_feats, feats_lens

###
def _load_model(package, classname, params=None, path=None):
    """
    """
    module = import_module(package)
    if path is not None:
        # load from the local file
        if '.pt' in path or '.pth' in path or '.ckpt' in path:
            model = getattr(module, classname)(**params)
            model.load_state_dict(torch.load(path, map_location=torch.device('cpu')), strict=False)
            print(f'[LOG]: load parameters from "{path}"')
        # huggingface
        else:
            model = getattr(module, classname).from_pretrained(path)
    else:
        model = getattr(module, classname)(**params)
        return model

        
    return model

###
class MissingDataInterface(AbsFrontend):
    """
    """
    @typechecked
    def __init__(
            self,
            fs: Union[int, str] = 16000,
            n_fft: int = 512,
            win_length: Optional[int] = None,
            hop_length: int = 128,
            window: Optional[str] = "hann",
            center: bool = True,
            normalized: bool = False,
            onesided: bool = True,
            n_mels: int = 80,
            fmin: Optional[int] = None,
            fmax: Optional[int] = None,
            htk: bool = False,                      
            apply_stft: bool = True,

            stft_domain: bool = True,
            configfile: Optional[str] = None,            
    ):
        super().__init__()
        
        if isinstance(fs, str):
            fs = humanfriendly.parse_size(fs)
            
        self.hop_length = hop_length

        if apply_stft is True:
            self.stft = Stft(
                n_fft=n_fft,
                win_length=win_length,
                hop_length=hop_length,
                center=center,
                window=window,
                normalized=normalized,
                onesided=onesided,
            )
        else:
            self.stft = None

        self.stft_domain = stft_domain

        ## configuration for enhancement
        with open(configfile, 'r') as f:
            conf = yaml.safe_load(f)
        
        self.enhmodel = None
        if conf.get('model') is not None:
            self.enhconf = conf['model']
        else:
            print('[ERROR]: speech-enhancement model is not specified. abort.')
            quit()

        ## sampler
        self.sampler = None
        self.sampler_name = None
        if (smpconf := conf.get('sampler')) is not None and smpconf.get("disable") is False:
            self.sampler_name = smpconf.get('name')
            if self.sampler_name == 'uniform':
                self.sampler = SamplerUniform(**smpconf['params'])
        
        self.logmel = LogMel(
            fs=fs,
            n_fft=n_fft,
            n_mels=n_mels,
            fmin=fmin,
            fmax=fmax,
            htk=htk,
        )
        self.n_mels = n_mels
        self.frontend_type = "default"
    
    def output_size(self) -> int:
        return self.n_mels

    def forward(
            self, input: torch.Tensor, input_lengths: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:

        # For STFT-domain model
        if self.stft_domain is True:
            if self.stft is not None:
                input_stft, feats_lens = self._compute_stft(input, input_lengths)
            else:
                input_stft = ComplexTensor(input[..., 0], input[..., 1])
                feats_lens = input_lengths

            # [Batch=1, Channel=1, TimeFrame, Freq=257]
            x = torch.abs(torch.complex(input_stft.real, input_stft.imag)).unsqueeze(0)

            # erasing the last frame
            x = x[:,:,0:-1,:]  
            feats_lens = feats_lens - 1

            #
            with torch.no_grad():
                # absolute spectrogram -> absolute spectrogram
                aspec, *_ = self.enhmodel(x)
                # aspec: [Batch=1, Channel=1, TimeFrame, Freq]

                # feature extraction of the enhanced speech spectrogram
                input_feats, _ = self.logmel(aspec.squeeze()**2)
                input_feats = input_feats.unsqueeze(0)

                if self.sampler is not None:
                    try:
                        # feature extraction of observed speech
                        obs_feat, _ = self.logmel(x.squeeze()**2)                                                
                        # generate samples for averaging
                        input_feats, feats_lens = self.sampler.draw(input_feats, obs_feat, feats_lens)
                        
                    except RuntimeError:
                        print('---- [ERROR]: RuntimeError')
                        quit()
            
            torch.cuda.empty_cache()

        # For time-domain model (not implemented)
        else:
            pass
            
        return input_feats, feats_lens

    # override (this may be dangerous)
    def _load_from_state_dict(
        self,
        state_dict,
        prefix,
        local_metadata,
        strict,
        missing_keys,
        unexpected_keys,
        error_msgs,
    ):
        # "state_dict" includes only "logmel" parameters of this class.
        device = state_dict.popitem()[1].device
        self.enhmodel = _load_model(**self.enhconf).to(device)
        print(f"[LOG]: finish loading \"{self.enhconf['classname']}\" class")

    
    # same method in "espnet2/asr/frontend/default.py"
    def _compute_stft(
            self, input: torch.Tensor, input_lengths: torch.Tensor
    ) -> torch.Tensor:
        input_stft, feats_lens = self.stft(input, input_lengths)        
        assert input_stft.dim() >= 4, input_stft.shape
        assert input_stft.shape[-1] == 2, input_stft.shape        
        input_stft = ComplexTensor(input_stft[..., 0], input_stft[..., 1])
        return input_stft, feats_lens
