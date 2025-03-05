#####
stage=0
device=cuda # cpu
kat_modeldir=models/espnet_ja_katakana_corpus10/
kan_modeldir=models/espnet_ja_kanakanji_corpus10/
####

###
# set symbolic link
if [ $stage -le 0 ]; then
  echo "---- stage 0 ----"
  ln -s ../models/ .
  ln -s ../data/ .
fi

###
# generate grammar fst
if [ $stage -le 1 ]; then
  echo "---- stage 1 ----"
  sh run.vis2fst.sh
fi

###
# convert wfst-lm format
if [ $stage -le 2 ]; then
  echo "---- stage 2 ----"
  for x in railroad_station railroad_any name_any; do
    ../script/launcher python3 mkwfst.py \
		       ${kat_modeldir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/config.yaml.update \
		       fst_model/${x}_final.config \
		       --textfile fst_model/${x}_final.fst \
		       --pklfile fst_model/${x}_final.bin
  done
fi

# recognize based on wfst-lm
if [ $stage -le 3 ]; then
  echo "---- stage 3 ----"
  ../script/launcher python3 wfstasr.py \
		     conf/decode.wfst.yaml \
		     --wavfiles data/audio/railroad01.flac data/audio/railroad02.flac data/audio/railroad03.flac  \
		     --asr_train_config ${kat_modeldir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/config.yaml.update \
		     --asr_model_file ${kat_modeldir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/valid.cer.ave_10best.pth \
		     --lm_train_config fst_model/railroad_station_final.config \
		     --device ${device} \
    | tee log.railroad_station.txt
  
  ../script/launcher python3 wfstasr.py \
		     conf/decode.wfst.yaml \
		     --wavfiles data/audio/railroad01.flac data/audio/railroad02.flac data/audio/railroad03.flac  \
		     --asr_train_config ${kat_modeldir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/config.yaml.update \
		     --asr_model_file ${kat_modeldir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/valid.cer.ave_10best.pth \
		     --lm_train_config fst_model/railroad_any_final.config \
		     --device ${device} \
    | tee log.railroad_any.txt

  ../script/launcher python3 wfstasr.py \
		     conf/decode.wfst.yaml \
		     --wavfiles data/audio/name01.flac \
		     --asr_train_config ${kat_modeldir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/config.yaml.update \
		     --asr_model_file ${kat_modeldir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/valid.cer.ave_10best.pth \
		     --lm_train_config fst_model/name_any_final.config \
		     --device ${device} \
    | tee log.name_any.txt

  cat log.*
fi

# recognize based on wfst-lm list
if [ $stage -le 4 ]; then
  echo "---- stage 4 ----"
  ../script/launcher python3 mkwfst.py \
  		     ${kat_modeldir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/config.yaml.update \
  		     fst_model/kat_default.config
  
  ../script/launcher python3 wfstasr.py \
		     conf/decode.wfst.yaml \
		     --wavlistfile trans_ambig/egs_key-path.txt \
		     --fstlistfile trans_ambig/egs_kat_key-fst.txt \
		     --asr_train_config ${kat_modeldir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/config.yaml.update \
		     --asr_model_file ${kat_modeldir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/valid.cer.ave_10best.pth \
		     --lm_train_config fst_model/kat_default.config \
		     --device ${device}
fi

# recognize based on wfst-lm list
if [ $stage -le 5 ]; then
  echo "---- stage 5 ----"
  ../script/launcher python3 mkwfst.py \
  		     ${kan_modeldir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/config.yaml.update \
  		     fst_model/kan_default.config
  
  ../script/launcher python3 wfstasr.py \
		     conf/decode.wfst.yaml \
		     --wavlistfile trans_ambig/egs_key-path.txt \
		     --fstlistfile trans_ambig/egs_kan_key-fst.txt \
		     --asr_train_config ${kan_modeldir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/config.yaml.update \
		     --asr_model_file ${kan_modeldir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/valid.cer.ave_10best.pth \
		     --lm_train_config fst_model/kan_default.config \
		     --device ${device}
fi
