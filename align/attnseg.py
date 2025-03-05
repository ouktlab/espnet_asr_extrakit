import torch
import soundfile
import numpy as np
from espnet2.tasks.asr import ASRTask
from espnet2.main_funcs.calculate_all_attentions import calculate_all_attentions

def usage():
   import argparse
   import yaml
   
   #
   parser = argparse.ArgumentParser(description='Attention Segmentation')
   parser.add_argument('asr_train_config')
   parser.add_argument('asr_model_file')

   #
   parser.add_argument('--audio_file')
   parser.add_argument('--trans_text')

   #
   parser.add_argument('--audio_list')
   parser.add_argument('--trans_list')
   
   parser.add_argument('--device', default='cuda')
   parser.add_argument('--dtype', default='float32')
   parser.add_argument('--thre', type=float, default=-1.5)
   parser.add_argument('--attnkey', type=str, default='decoder.decoders.5.src_attn')
   
   args = parser.parse_args()

   return args

def load_model(asr_train_config, asr_model_file, device, dtype):
   model, asr_train_args = ASRTask.build_model_from_file(
      asr_train_config, asr_model_file, device
   )
   model.to(dtype=getattr(torch, dtype)).eval()
   preprocess_fn = ASRTask.build_preprocess_fn(asr_train_args, False)   
   return model, preprocess_fn

def keypair2batch(preprocess_fn, key, audio_file, text, device, dtype):
   # only for one file :P
   text = torch.tensor(preprocess_fn(key, {"text": text})["text"]).reshape(1, -1).to(device=device)
   text_lengths = torch.tensor([len(x) for x in text]).to(device)
   
   speech, fs = soundfile.read(audio_file)
   if isinstance(speech, np.ndarray):
      speech = torch.tensor(speech)
      speech = speech.unsqueeze(0).to(device=device, dtype=getattr(torch, dtype))
   speech_lengths = speech.new_full([1], dtype=torch.long, fill_value=speech.size(1))   
   batch = {"speech": speech, "speech_lengths": speech_lengths, "text":text, "text_lengths":text_lengths}
   return batch, fs

def get_attention_weight(model, batch, thre, attnkey):
   """ 
   """
   att_dict = calculate_all_attentions(model, batch)
   att_w = att_dict[attnkey][0]
   
   # entropy-based head selection
   ents = []
   for w in att_w:
      ents.append(torch.mean(torch.sum(w * torch.log(w), dim=1)))
   ents = torch.tensor(ents)
   
   indices = torch.where(ents > thre)[0]
   if len(indices) == 0:
      indices = torch.argmax(ents).reshape(1)
   uni_att_w = torch.mean(att_w[indices], dim=0)
   uni_att_w = uni_att_w / torch.sum(uni_att_w, dim=0)   

   return uni_att_w

def get_lr_trace(tokens, uni_att_w):
   n_char, n_frame = uni_att_w.shape
   cost = torch.zeros([n_char, n_frame])
   trace = torch.zeros([n_char, n_frame], dtype=torch.int32)
   
   cost[0,0] = 1.0
   for t in range(1, n_frame):
      for c in range(n_char):
         stay_cost = cost[c][t-1] + uni_att_w[c][t] if t-1 >= 0 else 0
         trans_cost = cost[c-1][t-1] + uni_att_w[c][t] if c-1 >= 0 else 0
         trace[c][t] = 0 if stay_cost > trans_cost else -1 # flag of stay or trans
         cost[c][t] = stay_cost if stay_cost > trans_cost else trans_cost

   c = n_char - 1
   align_seq = []
   for t in range(n_frame-1,-1,-1):
      align_seq.insert(0, tokens[c])
      c += trace[c][t]
      
   return align_seq

def filtered_align(trans_text, uni_att_w, frame_sec):
   tokens = list(trans_text) + ['<sos/eos>']

   ###
   align_seq = get_lr_trace(tokens, uni_att_w)

   ###
   mod_seq = []
   token_len = 0
   for i, c in enumerate(align_seq):
      token_len += 1
      if i + 1 < len(align_seq) and c != align_seq[i+1]:
         mod_seq.append((c, token_len))
         token_len = 0
   mod_seq.append((align_seq[-1], token_len))

   ###
   segments = []
   n_acc = 0
   for c, l in mod_seq:
      segments.append((f'{frame_sec*n_acc:.2f}', f'{frame_sec*(n_acc+l):.2f}', f'{c:s}'))
      n_acc += l
   
   return segments

def proc_file(model, preprocess_fn, key, audio_file, trans_text, thre, attnkey, device, dtype):
   batch, fs = keypair2batch(preprocess_fn, key, audio_file, trans_text, device, dtype)   
   uni_att_w = get_attention_weight(model, batch, thre, attnkey)   
   frame_sec = batch['speech_lengths'][0] / uni_att_w.shape[1] / fs
   wavelen_sec =  batch['speech_lengths'][0] / fs
   segments = filtered_align(trans_text, uni_att_w, frame_sec)   
   return segments

def main():
   args = usage()

   if args.audio_file is not None and args.trans_text is not None:
      model, preprocess_fn = load_model(args.asr_train_config, args.asr_model_file, args.device, args.dtype)   
      segments = proc_file(model, preprocess_fn, 'dummy', args.audio_file, args.trans_text, args.thre, args.attnkey, args.device, args.dtype)

      print(f'file: {args.audio_file}')      
      for s, e, sym in segments:
         print(s, e, sym)
      
   elif args.audio_list is not None and args.trans_list is not None:
      model, preprocess_fn = load_model(args.asr_train_config, args.asr_model_file, args.device, args.dtype) 
      with open(args.audio_list) as af, open(args.trans_list) as tf:
         for audio, trans in zip(af, tf):
            key_a, audiofile = audio.strip().split(maxsplit=1)
            key_t, transtext = trans.strip().split(maxsplit=1)
            if key_a != key_t:
               print(f'[ERROR]: inconsistent key -- "{key_a}" and "{key_t}". skip.')
               continue
            segments = proc_file(model, preprocess_fn, key_a, audiofile, transtext, args.thre, args.attnkey, args.device, args.dtype)

            print(f'key: {key_a}, file: {audiofile}')
            for s, e, sym in segments:
               print(s, e, sym)
      
if __name__ == '__main__':
   main()
