#!/bin/bash

if [ $# -ne 2 ]; then
  echo "usage: version mode"
  exit;
fi

###
version=$1
mode=$2

### for patch files
espnet_model_src=${__ESPNET_ROOT}/espnet2/asr/espnet_model.py  
espnet_model_target=${__ESPNET_ROOT}/espnet2/asr/espnet_model_md.py  
espnet_model_patch=${__BASE_DIR}/${version}/espnet_model_md.py.patch

asr_src=${__ESPNET_ROOT}/espnet2/tasks/asr.py
asr_target=${__ESPNET_ROOT}/espnet2/tasks/asr_md.py
asr_patch=${__BASE_DIR}/${version}/asr_md.py.patch

inference_src=${__ESPNET_ROOT}/espnet2/bin/asr_inference.py  
inference_target=${__ESPNET_ROOT}/espnet2/bin/asr_inference_md.py  
inference_patch=${__BASE_DIR}/${version}/asr_inference_md.py.patch

md_target=${__ESPNET_ROOT}/espnet2/asr/frontend/md.py  
md_mod=${__BASE_DIR}/${version}/md.py

###
if [ $mode = "check" ]; then
  ls -l ${espnet_model_target}
  ls -l ${asr_target}
  ls -l ${inference_target}
  ls -l ${md_target}
fi

### install
if [ $mode = "install" ]; then
  if [ ! -e ${espnet_model_target} ]; then
    echo "  apply patch: " ${espnet_model_target} " " ${espnet_model_patch}
    patch -b -o ${espnet_model_target} ${espnet_model_src} ${espnet_model_patch}
  fi
  if [ ! -e ${asr_target} ]; then
    echo "  apply patch: " ${asr_target} " " ${asr_patch}
    patch -b -o ${asr_target} ${asr_src} ${asr_patch}
  fi
  if [ ! -e ${inference_target} ]; then
    echo "  apply patch: " ${inference_target} " " ${inference_patch}
    patch -b -o ${inference_target} ${inference_src} ${inference_patch}
  fi
  
   ### for wfst_lm.py
  if [ ! -e ${md_target} ]; then
    echo "  make symbolic link: " ${md_mod} "->" ${md_target}
    ln -s ${md_mod} ${md_target}
  fi

fi

### uninstall
if [ $mode = "uninstall" ]; then
  if [ -e ${espnet_model_target} ]; then
    echo "  remove ${espnet_model_target}"
    rm ${espnet_model_target}
  fi
  if [ -e ${asr_target} ]; then
    echo "  remove ${asr_target}"
    rm ${asr_target}
  fi
  if [ -e ${inference_target} ]; then
    echo "  remove ${inference_target}"
    rm ${inference_target}
  fi
  if [ -L ${md_target} ]; then
    echo "  remove symbolic link"
    rm ${md_target}
  fi

fi

