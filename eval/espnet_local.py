import torchaudio

def usage():
    """
    return
        args: argparse.Namespace
    """
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('asr_train_config', type=str, help='')
    parser.add_argument('asr_model_file', type=str, help='')
    parser.add_argument('lm_train_config', type=str, help='')
    parser.add_argument('lm_file', type=str, help='')

    parser.add_argument('keylistfile', type=str)
    parser.add_argument('resultfile', type=str)
    
    parser.add_argument('--basepath', type=str, default='.')
    parser.add_argument('--token_type', type=str, help='', default='char')
    parser.add_argument('--device', type=str, help='cpu or cuda', default='cpu')
    parser.add_argument('--nbest', type=int, help='nbest', default=5)
    parser.add_argument('--beam_size', type=int, help='beam size', default=40)
    parser.add_argument('--ctc_weight', type=float, help='nbest', default=0.3)
    parser.add_argument('--lm_weight', type=float, help='lm weight', default=0.1)
    parser.add_argument('--penalty', type=float, help='lm weight', default=0.0)

    args = parser.parse_args()
    return args
 
###
def proc_keylist(model, basepath, keylistfile, resultfile):
    with open(keylistfile, "r") as fkey, open(resultfile, "w") as rkey:
        for line in fkey:
            key, filepath = line.strip().split(maxsplit=1)

            s, fs = torchaudio.load(f'{basepath}/{filepath}')
            s = s.squeeze()
    
            print(f'[LOG]: now processing -- {key}')
            results = model(s)
            
            record = [key, results[0][0]]
            print('\t'.join(record), file=rkey, flush=True)

##
def main():
    args = usage()

    ##
    from espnet2.bin.asr_inference import Speech2Text
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
    
    proc_keylist(
        model,
        args.basepath, args.keylistfile,
        args.resultfile
    )        


if __name__ == '__main__':
    main()
    
