#!/bin/bash

if [ $# -ne 2 ]; then
  echo "usage: version mode"
  exit;
fi

###
version=$1
mode=$2

### for patch files
lm_target=${__ESPNET_ROOT}/espnet2/tasks/lm.py  
lm_patch=${__BASE_DIR}/${version}/lm.py.patch

### for new files
wfstlm_target=${__ESPNET_ROOT}/espnet2/lm/wfst_lm.py
wfstlm_mod=${__BASE_DIR}/${version}/wfst_lm.py

###
if [ $mode = "check" ]; then
  ls -l ${lm_target}
  ls -l ${wfstlm_target}
fi

### install
if [ $mode = "install" ]; then
  ### for lm.py
  if [ ! -e ${lm_target}.orig ]; then
    echo "  apply patch: " ${lm_target} " " ${lm_patch}
    patch -b ${lm_target} ${lm_patch}
  fi

  ### for wfst_lm.py
  if [ ! -e ${wfstlm_target} ]; then
    echo "  make symbolic link: " ${wfstlm_mod} "->" ${wfstlm_target}
    ln -s ${wfstlm_mod} ${wfstlm_target}
  fi

fi

### uninstall
if [ $mode = "uninstall" ]; then
  if [ -e ${lm_target}.orig ]; then
    echo "  unapply patch: " ${lm_target} " " ${lm_patch}
    patch -R ${lm_target} ${lm_patch}
    rm ${lm_target}.orig
  fi
  if [ -L ${wfstlm_target} ]; then
    echo "  remove symbolic link"
    rm ${wfstlm_target}
  fi

fi

