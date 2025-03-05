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

if [ $stage -le 1 ]; then
  echo "---- stage 1 ----"
  kat_text=…オンセー…ニンシキ…モデル…
  ../script/launcher python3 ctcseg.py \
		     ${kat_modeldir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/config.yaml.update \
		     ${kat_modeldir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/valid.cer.ave_10best.pth \
		     --audio_file data/audio/ambig01.flac \
		     --trans_text ${kat_text} \
  		     --device ${device}
fi

if [ $stage -le 2 ]; then
  echo "---- stage 2 ----"
  kan_text=…音声…認識…モデル… 
  ../script/launcher python3 ctcseg.py \
		     ${kan_modeldir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/config.yaml.update \
		     ${kan_modeldir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/valid.cer.ave_10best.pth \
		     --audio_file data/audio/ambig01.flac \
		     --trans_text ${kan_text} \
		     --device ${device}
fi

if [ $stage -le 3 ]; then
  echo "---- stage 3 ----"
  kat_text=…オンセー…ニンシキ…モデル…
  ../script/launcher python3 attnseg.py \
		     ${kat_modeldir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/config.yaml.update \
		     ${kat_modeldir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/valid.cer.ave_10best.pth \
		     --audio_file data/audio/ambig01.flac \
		     --trans_text ${kat_text} \
  		     --device ${device}
fi

if [ $stage -le 4 ]; then
  echo "---- stage 4 ----"
  kan_text=…音声…認識…モデル… 
  
  ../script/launcher python3 attnseg.py \
		     ${kan_modeldir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/config.yaml.update \
		     ${kan_modeldir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/valid.cer.ave_10best.pth \
		     --audio_file data/audio/ambig01.flac \
		     --trans_text ${kan_text} \
		     --device ${device}
fi

if [ $stage -le 5 ]; then
  echo "---- stage 5 ----"
  ../script/launcher python3 attnseg.py \
		     ${kat_modeldir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/config.yaml.update \
		     ${kat_modeldir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/valid.cer.ave_10best.pth \
		     --audio_list data/list/egs_align_key-path.txt \
		     --trans_list data/list/egs_align_key-text-kat.txt \
  		     --device ${device}
fi

if [ $stage -le 6 ]; then
  echo "---- stage 6 ----"
  ../script/launcher python3 attnseg.py \
		     ${kan_modeldir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/config.yaml.update \
		     ${kan_modeldir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/valid.cer.ave_10best.pth \
		     --audio_list data/list/egs_align_key-path.txt \
		     --trans_list data/list/egs_align_key-text-kan.txt \
  		     --device ${device}
fi
