#####
stage=0
device=cuda # cpu
kan_modeldir=models/espnet_ja_kanakanji_corpus10/
####

###
# set symbolic link
if [ $stage -le 0 ]; then
  echo "---- stage 0 ----"
  ln -s ../models/ .
  ln -s ../data/ .
fi

# recognize audio
if [ $stage -le 1 ]; then
  echo "---- stage 1 ----"
  ../script/launcher python3 cprobasr.py \
		     --wavfiles data/audio/railroad01.flac data/audio/railroad02.flac data/audio/railroad03.flac  \
		     --asr_train_config ${kan_modeldir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/config.yaml.update \
		     --asr_model_file ${kan_modeldir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/valid.cer.ave_10best.pth \
		     --lm_train_config ${kan_modeldir}/exp/lm_train_lm_ja_char/config.yaml \
		     --lm_file ${kan_modeldir}/exp/lm_train_lm_ja_char/valid.loss.ave_5best.pth \
		     --device ${device}
fi
