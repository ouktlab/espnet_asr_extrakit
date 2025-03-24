stage=0
device=cuda # cpu

#
if [ $stage -le 0 ]; then
  ln -s ../data .
fi

## recognition
if [ $stage -le 1 ]; then
  hfrepo=ouktlab/espnet_streaming_csj_asr_train_asr_transformer_lm_rnn
  ../script/launcher python3 streaming_asr.py \
		     --hfrepo ${hfrepo} \
		     --wavfiles \
		     data/audio/data021.flac \
		     data/audio/data022.flac \
		     data/audio/data023.flac
fi

if [ $stage -le 2 ]; then
  hfrepo=ouktlab/espnet_asr-ja-kc-stream_am-transformer-robustcorpus10_lm-transformer-corpus10-bccwj-wiki40b
  ../script/launcher python3 streaming_asr.py \
		     --hfrepo ${hfrepo} \
		     --wavfiles \
		     data/audio/data021.flac \
		     data/audio/data022.flac \
		     data/audio/data023.flac
fi
