import sys
import torch
import torchaudio

def usage():
    """
    return
        args: argparse.Namespace
    """
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--hfrepo', type=str, default='ouktlab/espnet_streaming_csj_asr_train_asr_transformer_lm_rnn')
 
    parser.add_argument('--wavfiles', nargs='*')
    parser.add_argument('--token_type', type=str, help='', default='char')
    parser.add_argument('--device', type=str, help='cpu or cuda', default='cpu')
    parser.add_argument('--nbest', type=int, help='nbest', default=5)
    parser.add_argument('--beam_size', type=int, help='beam size', default=10)
    parser.add_argument('--ctc_weight', type=float, help='nbest', default=0.3)
    parser.add_argument('--lm_weight', type=float, help='lm weight', default=0.1)
    parser.add_argument('--penalty', type=float, help='lm weight', default=0.0)

    args = parser.parse_args()
    return args

def recognize_wavlist(model, wavlists):
    import time
    
    records = []
    segment_len = 1600

    for filename in wavlists:
        print('[LOG]:', filename)
        s, fs = torchaudio.load(filename)
        s = s.squeeze()
        wave_time = len(s)/fs
        
        time_beg = time.perf_counter()
        for pos in range(0, len(s), segment_len):
            segment = s[pos:pos+segment_len]
            results = model(segment, is_final=False)

            if results is not None and len(results) > 0:
                nbests = [text for text, token, token_int, hyp in results]
                text = nbests[0] if nbests is not None and len(nbests) > 0 else ""
                print(f'[LOG]: real-time result -- {text}\r', file=sys.stderr, flush=True, end='')
        
        print('', file=sys.stderr, flush=True)
        results = model(torch.empty(0), is_final=True)
        proc_time = time.perf_counter() - time_beg

        nbests = [text for text, token, token_int, hyp in results]
        print(f'[LOG]: N-best results')
        for x in nbests:
            print(f'[LOG]:   {x}')
        

    return records

##
def main():
    args = usage()

    ##
    from espnet2.bin.asr_inference_streaming import Speech2TextStreaming
    model = Speech2TextStreaming.from_pretrained(
        args.hfrepo,
        device=args.device,
        token_type=args.token_type,
        bpemodel=None,
        maxlenratio=0.0,
        minlenratio=0.0,
        beam_size=args.beam_size,
        nbest=args.nbest,
        ctc_weight=args.ctc_weight,
        lm_weight=args.lm_weight,
        penalty=0.0,
        disable_repetition_detection=True,
    )
    
    recognize_wavlist(model, args.wavfiles)


if __name__ == '__main__':
    main()
    
