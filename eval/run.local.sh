stage=0
device=cuda # cpu

#
if [ $stage -le 0 ]; then
  ln -s ../models .
  ln -s ../data .
  ln -s ../exp .
fi

#
modeldir=models/espnet_ja_kanakanji_corpus10/
resultdir=exp/asr_recog/

## recognition
if [ $stage -le 1 ]; then
  ../script/launcher python3 espnet_local.py \
		     ${modeldir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/config.yaml.update \
		     ${modeldir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/valid.cer.ave_10best.pth \
		     ${modeldir}/exp/lm_train_lm_ja_char/config.yaml \
		     ${modeldir}/exp/lm_train_lm_ja_char/valid.loss.ave_5best.pth \
		     data/list/egs_train_key-path.txt \
		     ${resultdir}/list_asr_result.txt \
		     --device ${device}
fi

## score (CER) calculation
if [ $stage -le 2 ]; then
  # ref
  cat data/list/egs_train_key-text.txt \
    | python3 trn2evalfmt.py > ${resultdir}/ref.txt

  # hyp
  cat ${resultdir}/list_asr_result.txt \
    | python3 trn2evalfmt.py > ${resultdir}/hyp.txt

  #
  ../script/launcher sclite \
		     -r ${resultdir}/ref.txt trn \
		     -h ${resultdir}/hyp.txt trn \
		     -i rm -o all stdout > ${resultdir}/score.txt
fi

