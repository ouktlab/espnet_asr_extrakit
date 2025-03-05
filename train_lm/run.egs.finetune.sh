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
		     conf/egs_train_lm_rnn.yaml \
		     exp/egs_pretrained/pretrained_lm_model.pth \
		     ${stage_st}
fi
