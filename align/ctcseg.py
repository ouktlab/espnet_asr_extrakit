import torch
import torchaudio
import numpy as np
from espnet2.bin.asr_align import CTCSegmentation

def usage():
   import argparse
   
   #
   parser = argparse.ArgumentParser(description='Attention Segmentation')
   parser.add_argument('asr_train_config')
   parser.add_argument('asr_model_file')
   parser.add_argument('--audio_file')
   parser.add_argument('--trans_text')
   parser.add_argument('--audio_list')
   parser.add_argument('--trans_list')
   parser.add_argument('--device', default='cuda')
   
   args = parser.parse_args()
   
   return args

def text2charlab(text):
    labels = []
    for i, c in enumerate(list(text)):
        labels.append(f'{i:d} {c:s}')
    return labels

def load_model(asr_train_config, asr_model_file):
   model = CTCSegmentation(asr_train_config, asr_model_file)
   model.set_config(gratis_blank=True)   
   return model

def main():
   ##
   args = usage()
   
   #

   if args.audio_file is not None and args.trans_text is not None:      
      model  = load_model(args.asr_train_config, args.asr_model_file)
      # 
      charlab = text2charlab(args.trans_text)
      s, fs = torchaudio.load(args.audio_file)
      # 
      segments = model(s.squeeze(), charlab, fs=fs)

      print(f'file: {args.audio_file}')
      for line in str(segments).split('\n'):
         tokens = line.split()
         if len(tokens) > 2:
            print(f'{float(tokens[2]):.2f} {float(tokens[3]):.2f} {tokens[5]}')

   elif args.audio_list is not None and args.trans_list is not None:
      model  = load_model(args.asr_train_config, args.asr_model_file)
      with open(args.audio_list) as af, open(args.trans_list) as tf:
         for audio, trans in zip(af, tf):
            key_a, audiofile = audio.strip().split(maxsplit=1)
            key_t, transtext = trans.strip().split(maxsplit=1)
            if key_a != key_t:
               print(f'[ERROR]: inconsistent key -- "{key_a}" and "{key_t}". skip.')
               continue
            charlab = text2charlab(transtext)
            s, fs = torchaudio.load(audiofile)
            # 
            segments = model(s.squeeze(), charlab, fs=fs)

            print(f'key: {key_a}, file: {audiofile}')
            for line in str(segments).split('\n'):
               tokens = line.split()
               if len(tokens) > 2:
                  print(f'{float(tokens[2]):.2f} {float(tokens[3]):.2f} {tokens[5]}')

if __name__ == '__main__':
   main()
