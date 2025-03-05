stage=0
device=cuda

if [ $stage -le 0 ]; then
  echo "---- stage 0 ----"
  ln -s ../models/ .
  ln -s ../data/ .
fi

if [ $stage -le 1 ]; then
  modeldir=models/espnet_ja_kanakanji_csj/

  ../script/launcher python3 mdasr.py \
                     ${modeldir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/config.yaml.update \
                     ${modeldir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/valid.acc.ave_10best.pth \
                     ${modeldir}/exp/lm_train_lm_ja_char/config.yaml \
                     ${modeldir}/exp/lm_train_lm_ja_char/valid.loss.ave.pth \
  		     --wavfiles data/audio/data021_noisy.flac data/audio/data022_noisy.flac data/audio/data023_noisy.flac \
                     --device ${device} \
   		     --disable_md
  
  ../script/launcher python3 mdasr.py \
                     ${modeldir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/config.enh.wosmp.yaml \
                     ${modeldir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/valid.acc.ave_10best.pth \
                     ${modeldir}/exp/lm_train_lm_ja_char/config.yaml \
                     ${modeldir}/exp/lm_train_lm_ja_char/valid.loss.ave.pth \
		     --wavfiles data/audio/data021_noisy.flac data/audio/data022_noisy.flac data/audio/data023_noisy.flac \
                     --device ${device}

  ../script/launcher python3 mdasr.py \
                     ${modeldir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/config.enh.yaml \
                     ${modeldir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/valid.acc.ave_10best.pth \
                     ${modeldir}/exp/lm_train_lm_ja_char/config.yaml \
                     ${modeldir}/exp/lm_train_lm_ja_char/valid.loss.ave.pth \
		     --wavfiles data/audio/data021_noisy.flac data/audio/data022_noisy.flac data/audio/data023_noisy.flac \
                     --device ${device}
  exit;
fi
