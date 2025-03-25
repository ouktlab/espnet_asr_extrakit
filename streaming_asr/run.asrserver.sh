##
stage=0
device=cuda # cpu

## recognition
if [ $stage -le 1 ]; then
  hfrepo=ouktlab/espnet_streaming_csj_asr_train_asr_transformer_lm_rnn
  
  ../script/launcher python3 adinASRserver.py \
		     ${hfrepo}
fi
