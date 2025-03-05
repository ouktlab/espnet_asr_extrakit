from espnet2.bin.asr_inference import Speech2Text
import torchaudio


class Speech2TextWFSTInterface(Speech2Text):
    '''
    '''
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._wfst = self.beam_search.scorers['lm'].wfst
        
    def reload(self, wfstfile):
         self._wfst.reload(wfstfile)

    def __call__(self, audio):
        results = super().__call__(audio)
        for text, token, token_int, hyp in results:
            maxscore, hypset = self._wfst.finalize_hyp(hyp[3]['lm']['hypset'])
            wfst_texts = [','.join(self._wfst.shrink_osyms(x.osyms)) for x in hypset]
            hyp[3]['lm']['subtexts'] = wfst_texts
            hyp[3]['lm']['score'] = maxscore

        return results

'''
'''
def recognize_wavlist(model, wavlists, writer=None, memorize=False):
    import time
    
    records = []
    for filename in wavlists:
        print('[LOG]:', filename)
        s, fs = torchaudio.load(filename)
        s = s.squeeze()

        time_beg = time.perf_counter()
        results = model(s)
        proc_time = time.perf_counter() - time_beg
        wave_time = len(s)/fs

        if writer is not None:
            writer(results, proc_time, wave_time)            
        if memorize is True:
            records.append((record, proc_time, wave_time, filename))

    return records


def recognize_pairedlist(model, wavlistfile, fstlistfile, writer=None, memorize=False):
    import time
    
    records = []
    with open(wavlistfile) as wavf, open(fstlistfile) as fstf:
        for wavline, fstline in zip(wavf, fstf):
            key_wav, wavfile = wavline.strip().split()
            key_fst, fstfile = fstline.strip().split()
            
            print('[LOG]:', wavfile, fstfile)
            s, fs = torchaudio.load(wavfile)
            s = s.squeeze()
            
            model.reload(fstfile)
            time_beg = time.perf_counter()
            results = model(s)
            proc_time = time.perf_counter() - time_beg            
            wave_time = len(s)/fs

            if writer is not None:
                writer(results, proc_time, wave_time)            
            if memorize is True:
                records.append((record, proc_time, wave_time, filename))

    return records

def wfst_1best_print(results, proc_time, wave_time):
    for text, token, token_int, hyp in results:
        print(f'[LOG]: RTF={proc_time/wave_time:.2f}, Score={hyp[1].item():.3f}, text={text}')
        for x in hyp[3]['lm']['subtexts']:
            print(f'[LOG]: {x}')
        break

##
def usage():
    import argparse
    import yaml

    #
    parser = argparse.ArgumentParser(description='server asr')
    parser.add_argument('config', help='yaml file for default decoding configuration [in]')
    parser.add_argument('--wavfiles', help='list of wavefiles with key [in]', nargs='*')
    parser.add_argument('--asr_train_config', type=str)
    parser.add_argument('--asr_model_file', type=str)
    parser.add_argument('--lm_train_config', type=str)
    parser.add_argument('--lm_file', type=str)
    parser.add_argument('--beam_size', type=int)
    parser.add_argument('--ctc_weight', type=float)
    parser.add_argument('--lm_weight', type=float)
    parser.add_argument('--device', type=str)
    parser.add_argument('--nbest', type=int)
    parser.add_argument('--wavlistfile', type=str)
    parser.add_argument('--fstlistfile', type=str)

    #
    paramnames = ['asr_train_config', 'asr_model_file', 'lm_train_config', 'lm_file',
                  'beam_size', 'ctc_weight', 'lm_weight', 'device', 'nbest']

    args = parser.parse_args()

    # default settings
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)

    args_dict = vars(args)
    for x in paramnames:
        config[x] = args_dict[x] if args_dict[x] is not None else config[x]

    return args, config

##
def main():
    #
    args, config = usage()
    
    # 
    model = Speech2TextWFSTInterface(**config)

    #
    if args.wavfiles is not None:
        recognize_wavlist(model, args.wavfiles, writer=wfst_1best_print)
    elif args.wavlistfile is not None and args.fstlistfile is not None:
        recognize_pairedlist(model, args.wavlistfile, args.fstlistfile, writer=wfst_1best_print)


##
if __name__ == '__main__':
    main()
