#
if [ $# -le 1 ]; then
  echo "usage: basedir config [stage]"
  exit;
fi

####
if [ "$3" != "" ]; then
  stage=$3
else
  stage=0
fi

###
basedir=$1
config=$2

####
lmdir=${basedir}/lm/

listdir=${basedir}/lists/
token_list=${basedir}/tokens.txt

####
train_key_txt=${listdir}/train_key-text.txt
valid_key_txt=${listdir}/valid_key-text.txt

train_key_flt_txt=${listdir}/train_key-flttext.txt
valid_key_flt_txt=${listdir}/valid_key-flttext.txt

train_shape_txt=${listdir}/train_key-shape.txt
valid_shape_txt=${listdir}/valid_key-shape.txt

# stats
if [ $stage -le 0 ]; then
    echo "---- stage 0 ----"
    if [ ! -e ${token_list} ]; then
      cat ${train_key_txt} | python3 ../script/gettoken.py \
    				     > ${token_list}
    fi
    ntoken=`wc ${token_list} | awk '{print $1}'`
    echo "# of tokens: " $ntoken
    cat ${train_key_txt} | python3 ../script/char2shape.py ${ntoken} \
				   ${train_key_flt_txt} ${train_shape_txt}
    cat ${valid_key_txt} | python3 ../script/char2shape.py ${ntoken} \
				   ${valid_key_flt_txt} ${valid_shape_txt}
fi

# 
if [ $stage -le 1 ]; then
    echo "---- stage 1 ----"
    python3 -m espnet2.bin.lm_train \
	    --ngpu 1 \
	    --use_preprocessor true \
	    --bpemodel none \
	    --token_type char \
	    --token_list ${token_list} \
	    --non_linguistic_symbols none \
	    --cleaner none \
	    --resume true \
	    --g2p none \
	    --train_shape_file ${train_shape_txt} \
	    --valid_shape_file ${valid_shape_txt} \
	    --train_data_path_and_name_and_type ${train_key_flt_txt},text,text \
	    --valid_data_path_and_name_and_type ${valid_key_flt_txt},text,text \
	    --fold_length 150 \
	    --output_dir ${lmdir} \
	    --config ${config} \
	    --multiprocessing_distributed True \
	    2>&1 | tee ${lmdir}/log.txt
fi
