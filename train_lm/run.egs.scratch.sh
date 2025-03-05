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
  ../script/launcher sh egs.train.single.sh \
		     exp/egs_scratch/ \
		     conf/egs_train_lm_transformer.yaml \
		     ${stage_st}
fi
