#!/bin/bash

if [ $# -ne 2 ]; then
  echo "usage: version mode"
  exit;
fi

###
version=$1
mode=$2

### for patch files
inference_target=${__ESPNET_ROOT}/espnet2/bin/asr_inference_streaming.py
inference_patch=${__BASE_DIR}/${version}/asr_inference_streaming.py.patch

###
if [ $mode = "check" ]; then
  ls -l ${inference_target}
fi

### install
if [ $mode = "install" ]; then
  if [ ! -e ${inference_target}.orig ]; then
    echo "  apply patch: " ${inference_target} " " ${inference_patch}
    patch -b ${inference_target} ${inference_patch}
  fi
fi

### uninstall
if [ $mode = "uninstall" ]; then
  if [ -e ${inference_target}.orig ]; then
    echo "  unapply patch ${inference_target} ${inference_path}"
    patch -R ${inference_target} ${inference_patch}
    rm ${inference_target}.orig
  fi

fi

