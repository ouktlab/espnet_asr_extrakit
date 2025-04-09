#####
python=python3.10
stage=1

enable_train=true
enable_eval=true
enable_wfst=  # true
enable_mdasr=true

###########################################################
# Common Settings
###########################################################
# set up local ESPnet and edit launcher
if [ $stage -le 0 ]; then
  echo "---- stage 0 ----"
  git clone https://github.com/espnet/espnet.git
  cd espnet
  cd tools
  ./setup_venv.sh $(command -v python3)
  make

  cd ../../
  # cp script/launcher.tmpl script/launcher
  # emacs -nw script/launcher
  exit;
fi

###########################################################
# For Model Training
###########################################################
# example of training from scratch
if [ "${enable_train}" = "true" ] && [ $stage -le 1 ]; then
  echo "---- stage 1 ----"
  unzip data.zip
  
  ###
  # make working directory
  mkdir -p exp/egs_scratch/
  cd exp/egs_scratch/
  mkdir -p stats lists am lm
  cd lists/

  # set symbolic links
  if [ ! -e train_key-path.txt ]; then
    ln -s ../../../data/list/egs_train_key-path.txt train_key-path.txt
  fi
  if [ ! -e train_key-text.txt ]; then
    ln -s ../../../data/list/egs_train_key-text.txt train_key-text.txt
  fi
  if [ ! -e valid_key-path.txt ]; then
    ln -s ../../../data/list/egs_valid_key-path.txt valid_key-path.txt
  fi
  if [ ! -e valid_key-text.txt ]; then
    ln -s ../../../data/list/egs_valid_key-text.txt valid_key-text.txt
  fi
  cd ../../../
  ###

fi

# example of training from pre-trained model
if [ "${enable_train}" = "true" ] && [ $stage -le 2 ]; then
  echo "---- stage 2 ----"
  hfrepo=ouktlab/espnet_csj_asr_train_asr_transformer_lm_rnn
  download_dir=models/espnet_ja_kanakanji_csj/
  
  # download ASR model
  if [ ! -d ${download_dir} ]; then
    sudo apt install git-lfs
    git lfs install  

    mkdir -p models
    git clone \
    	https://huggingface.co/${hfrepo} \
    	${download_dir}
    
    cat ${download_dir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/config.yaml \
      | sed -e 's|exp/asr_stats_raw_jp_char_sp/train/feats_stats.npz|'${download_dir}'/exp/asr_stats_raw_jp_char_sp/train/feats_stats.npz|' \
	    > ${download_dir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/config.yaml.update
    
    cat ${download_dir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/config.yaml.update \
      | sed -e 's|frontend: default|frontend: md|' \
      | sed -e 's|frontend_conf:|frontend_conf:\n    configfile: conf/enh.config|' \
	    >  ${download_dir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/config.enh.yaml
    cat ${download_dir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/config.enh.yaml \
      | sed -e 's|configfile: conf/enh.config|configfile: conf/enh.wosmp.config|' \
	    >  ${download_dir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/config.enh.wosmp.yaml
  fi
  
  ###
  # make working directory
  mkdir -p exp/egs_pretrained/
  cd exp/egs_pretrained/
  mkdir -p stats lists am lm
  cd lists/

  # set symbolic links
  if [ ! -e train_key-path.txt ]; then
    ln -s ../../../data/list/egs_train_key-path.txt train_key-path.txt
  fi
  if [ ! -e train_key-text.txt ]; then
    ln -s ../../../data/list/egs_train_key-text.txt train_key-text.txt
  fi
  if [ ! -e valid_key-path.txt ]; then
    ln -s ../../../data/list/egs_valid_key-path.txt valid_key-path.txt
  fi
  if [ ! -e valid_key-text.txt ]; then
    ln -s ../../../data/list/egs_valid_key-text.txt valid_key-text.txt
  fi
  cd ../../../
  ###

  ## set up configuration
  ./script/launcher python3 script/extracttoken.py \
	     ${download_dir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/config.yaml \
    | grep -v LAUNCH \
	   > exp/egs_pretrained/tokens.txt

  ####
  # set symbolic links
  cd exp/egs_pretrained/
  if [ ! -e pretrained_asr_model.pth ]; then
    ln -s ../../${download_dir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/valid.acc.ave_10best.pth \
       pretrained_asr_model.pth
  fi
  if [ ! -e pretrained_lm_model.pth ]; then
    ln -s ../../${download_dir}/exp/lm_train_lm_ja_char/valid.loss.ave.pth \
       pretrained_lm_model.pth
  fi
  if [ ! -e pretrained_feats_stat.npz ]; then
    ln -s ../../${download_dir}/exp/asr_stats_raw_jp_char_sp/train/feats_stats.npz \
       pretrained_feats_stat.npz
  fi  
  cd ../../
  ####
  
fi


###########################################################
# For CER evaluation
###########################################################
if [ "${enable_eval}" = "true" ] && [ $stage -le 3 ]; then
  echo "---- stage 3 ----"
  ###
  hfrepo=ouktlab/espnet_asr-ja-mc_am-transformer-robustcorpus10_lm-transformer-corpus10-bccwj-wiki40b
  download_dir=models/espnet_ja_kanakanji_corpus10/
  
  # download ASR model
  if [ ! -d ${download_dir} ]; then
    mkdir -p models
    git clone \
	https://huggingface.co/${hfrepo} \
	${download_dir}
    
    cat ${download_dir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/config.yaml \
      | sed -e 's|exp/asr_stats_raw_jp_char_sp/train/feats_stats.npz|'${download_dir}'/exp/asr_stats_raw_jp_char_sp/train/feats_stats.npz|' \
	    > ${download_dir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/config.yaml.update
  else
    echo "  skip downloading a model: already exist: \"${download_dir}\""
  fi

  ###
  hfrepo=ouktlab/espnet_asr-ja-kc_am-transformer-robustcorpus10_lm-transformer-corpus10-bccwj-wiki40b
  download_dir=models/espnet_ja_katakana_corpus10/
  
  # download ASR model
  if [ ! -d ${download_dir} ]; then
    mkdir -p models
    git clone \
	https://huggingface.co/${hfrepo} \
	${download_dir}
    
    cat ${download_dir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/config.yaml \
      | sed -e 's|exp/asr_stats_raw_jp_char_sp/train/feats_stats.npz|'${download_dir}'/exp/asr_stats_raw_jp_char_sp/train/feats_stats.npz|' \
	    > ${download_dir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/config.yaml.update
  else
    echo "  skip downloading a model: already exist: \"${download_dir}\""
  fi
fi

if [ "${enable_wfst}" = "true" ] && [ $stage -le 4 ]; then
  echo "---- stage 4 ----"
  mkdir -p exp/asr_recog/
fi


###########################################################
# For WFST ASR
###########################################################
if [ "${enable_wfst}" = "true" ] && [ $stage -le 5 ]; then
  echo "---- stage 5 ----"
  sudo apt-get install ${python}-tk libfst-tools chromium-browser
  ${python} -m venv venv
  . venv/bin/activate
  ${python} -m pip install eel pytk pyyaml

fi

if [ "${enable_wfst}" = "true" ] && [ $stage -le 6 ]; then
  echo "---- stage 6 ----"
  hfrepo=ouktlab/espnet_asr-ja-kc_am-transformer-robustcorpus10_lm-transformer-corpus10-bccwj-wiki40b
  download_dir=models/espnet_ja_katakana_corpus10/
  
  # download ASR model
  if [ ! -d ${download_dir} ]; then
    mkdir -p models
    git clone \
	https://huggingface.co/${hfrepo} \
	${download_dir}
    
    cat ${download_dir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/config.yaml \
      | sed -e 's|exp/asr_stats_raw_jp_char_sp/train/feats_stats.npz|'${download_dir}'/exp/asr_stats_raw_jp_char_sp/train/feats_stats.npz|' \
	    > ${download_dir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/config.yaml.update
  fi
fi

if [ "${enable_wfst}" = "true" ] && [ $stage -le 7 ]; then
  echo "---- stage 7 ----"
  hfrepo=ouktlab/espnet_asr-ja-mc_am-transformer-robustcorpus10_lm-transformer-corpus10-bccwj-wiki40b
  download_dir=models/espnet_ja_kanakanji_corpus10/
  
  # download ASR model
  if [ ! -d ${download_dir} ]; then
    mkdir -p models
    git clone \
	https://huggingface.co/${hfrepo} \
	${download_dir}
    cat ${download_dir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/config.yaml \
      | sed -e 's|exp/asr_stats_raw_jp_char_sp/train/feats_stats.npz|'${download_dir}'/exp/asr_stats_raw_jp_char_sp/train/feats_stats.npz|' \
	    > ${download_dir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/config.yaml.update
  fi
fi


###########################################################
# For MD ASR
###########################################################
if [ "${enable_mdasr}" = "true" ] && [ $stage -le 8 ]; then
  echo "---- stage 8 ----"
  hfrepo=ouktlab/espnet_csj_asr_train_asr_transformer_lm_rnn
  download_dir=models/espnet_ja_kanakanji_csj/
  
  # download ASR model
  if [ ! -d ${download_dir} ]; then
    mkdir -p models
    git clone \
    	https://huggingface.co/${hfrepo} \
    	${download_dir}
  
    cat ${download_dir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/config.yaml \
      | sed -e 's|exp/asr_stats_raw_jp_char_sp/train/feats_stats.npz|'${download_dir}'/exp/asr_stats_raw_jp_char_sp/train/feats_stats.npz|' \
	    > ${download_dir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/config.yaml.update
    cat ${download_dir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/config.yaml.update \
      | sed -e 's|frontend: default|frontend: md|' \
      | sed -e 's|frontend_conf:|frontend_conf:\n    configfile: conf/enh.config|' \
	    >  ${download_dir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/config.enh.yaml
    cat ${download_dir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/config.enh.yaml \
      | sed -e 's|configfile: conf/enh.config|configfile: conf/enh.wosmp.config|' \
	    >  ${download_dir}/exp/asr_train_asr_transformer_ja_raw_jp_char_sp/config.enh.wosmp.yaml
  fi
  
  ./script/launcher python3 -m pip install safetensors
fi
