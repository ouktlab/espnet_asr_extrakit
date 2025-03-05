#
if [ $# -le 3 ]; then
  echo "usage: basedir config pretraind_model pretrained_feats_stat [stage]"
  exit;
fi

####
if [ "$5" != "" ]; then
  stage=$5
else
  stage=0
fi

####
basedir=$1
config=$2
pretrained_model=$3
pretrained_feats_stat=$4

####
statdir=${basedir}/stats/
listdir=${basedir}/lists/
amdir=${basedir}/am/

token_list=${basedir}/tokens.txt

####
train_key_wav=${listdir}/train_key-path.txt
train_key_txt=${listdir}/train_key-text.txt
valid_key_wav=${listdir}/valid_key-path.txt
valid_key_txt=${listdir}/valid_key-text.txt

####
if [ $stage -le 0 ]; then
  echo "---- stage 0 ----"
  python3 -m espnet2.bin.asr_train \
	  --collect_stats true \
	  --use_preprocessor true \
	  --bpemodel none \
	  --token_type char \
	  --token_list ${token_list} \
	  --non_linguistic_symbols none \
	  --cleaner none \
	  --g2p none \
	  --train_shape_file ${train_key_wav} \
	  --valid_shape_file ${valid_key_wav} \
	  --output_dir ${statdir} \
	  --config ${config} \
	  --frontend_conf fs=16k \
	  --train_data_path_and_name_and_type ${train_key_wav},speech,sound \
	  --valid_data_path_and_name_and_type ${valid_key_wav},speech,sound \
	  --train_data_path_and_name_and_type ${train_key_txt},text,text \
	  --valid_data_path_and_name_and_type ${valid_key_txt},text,text \
	  2>&1 | tee ${statdir}/log.txt
  
  <"${statdir}/train/text_shape" \
   awk -v N="$(<${token_list} wc -l)" '{ print $0 "," N }' \
   > ${statdir}/train/text_shape.char
  
  <"${statdir}/valid/text_shape" \
   awk -v N="$(<${token_list} wc -l)" '{ print $0 "," N }' \
   > ${statdir}/valid/text_shape.char
  
fi

if [ $stage -le 1 ]; then
  echo "---- stage 1 ----"
  python3 -m espnet2.bin.asr_train \
	  --use_preprocessor true \
	  --bpemodel none \
	  --token_type char \
	  --token_list ${token_list} \
	  --non_linguistic_symbols none \
	  --cleaner none \
	  --g2p none \
	  --resume true \
	  --ignore_init_mismatch false \
	  --fold_length 80000 \
	  --output_dir ${amdir} \
	  --config ${config} \
	  --frontend_conf fs=16k \
	  --normalize=global_mvn \
	  --normalize_conf stats_file=${pretrained_feats_stat} \
	  --train_data_path_and_name_and_type ${train_key_wav},speech,sound \
	  --train_shape_file ${statdir}/train/speech_shape \
	  --valid_data_path_and_name_and_type ${valid_key_wav},speech,sound \
	  --valid_shape_file ${statdir}/valid/speech_shape \
	  --fold_length 150 \
	  --train_data_path_and_name_and_type ${train_key_txt},text,text \
	  --train_shape_file ${statdir}/train/text_shape.char \
	  --valid_data_path_and_name_and_type ${valid_key_txt},text,text \
	  --valid_shape_file ${statdir}/valid/text_shape.char \
	  --ngpu 1 --multiprocessing_distributed True \
	  --init_param ${pretrained_model} \
	  2>&1 | tee ${amdir}/log.txt
  
  
fi
