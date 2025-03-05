##
stage=0

## prepare
if [ $stage -le 0 ]; then
  if [ ! -e data ]; then
    ln -s ../data
  fi
  if [ ! -e exp ]; then
    ln -s ../exp
  fi
fi

## train
if [ $stage -le 1 ]; then
  stage_st=0
  ../script/launcher sh egs.finetune.single.sh \
	     exp/egs_pretrained/ \
	     conf/egs_train_asr_transformer_fixedlr.yaml \
	     exp/egs_pretrained/pretrained_asr_model.pth \
	     exp/egs_pretrained/pretrained_feats_stat.npz \
	     ${stage_st}
fi
