from espnet2.bin.asr_inference import Speech2Text
import torchaudio

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

import unicodedata
def cprob_1best_print(results, proc_time, wave_time):
    for text, token, token_int, hyp in results:
        print(f'[LOG]: RTF={proc_time/wave_time:.2f}, Score={hyp[1].item():.3f}, text={text}, ', end='')
        for key, value in hyp[2].items():            
            print(f'{key}={value:.3f}', end=', ')
        print('')

        print(f'chars  : ', end='')
        for c in list(text):
            if unicodedata.east_asian_width(c) == 'A':
                print(f'{c:6s}', end=' ')
            else:
                print(f'{c:5s}', end=' ')
        print('<sos/eos>   SUM')
        for key, value in hyp[4].items():
            print(f'{key:7s}: ', end='')
            for x in value.tolist():
                print(f'{x:.3f}', end=' ')
            print(f' -- {sum(value):.3f}')
        break

##
def usage():
    import argparse
    import yaml

    #
    parser = argparse.ArgumentParser(description='server asr')
    parser.add_argument('--wavfiles', help='list of wavefiles with key [in]', nargs='*')
    parser.add_argument('--asr_train_config', type=str)
    parser.add_argument('--asr_model_file', type=str)
    parser.add_argument('--lm_train_config', type=str)
    parser.add_argument('--lm_file', type=str)
    parser.add_argument('--beam_size', type=int, default=20)
    parser.add_argument('--ctc_weight', type=float, default=0.1)
    parser.add_argument('--lm_weight', type=float, default=0.1)
    parser.add_argument('--device', type=str, default='cpu')
    parser.add_argument('--token_type', type=str, default='char')
    parser.add_argument('--nbest', type=int, default=3)

    #
    args = parser.parse_args()

    return args

##
def main():
    #
    args = usage()
    
    # 
    model = Speech2Text(
        asr_train_config=args.asr_train_config,
        asr_model_file=args.asr_model_file,
        lm_train_config=args.lm_train_config,
        lm_file=args.lm_file,
        device=args.device,
        token_type=args.token_type,
        bpemodel=None,
        maxlenratio=0.0,
        minlenratio=0.0,
        beam_size=args.beam_size,
        nbest=args.nbest,
        ctc_weight=args.ctc_weight,
        lm_weight=args.lm_weight,
        penalty=0.0
    )

    #
    recognize_wavlist(model, args.wavfiles, writer=cprob_1best_print)


##
if __name__ == '__main__':
    main()
