#!/bin/bash

if [ $# -ne 2 ]; then
  echo "usage: version mode"
  exit;
fi

###
version=$1
mode=$2

### for patch files
beamsearch_target=${__ESPNET_ROOT}/espnet/nets/beam_search.py
beamsearch_patch=${__BASE_DIR}/${version}/beam_search.py.patch

batchbeamsearch_target=${__ESPNET_ROOT}/espnet/nets/batch_beam_search.py
batchbeamsearch_patch=${__BASE_DIR}/${version}/batch_beam_search.py.patch

batchbeamsearchonline_target=${__ESPNET_ROOT}/espnet/nets/batch_beam_search_online.py
batchbeamsearchonline_patch=${__BASE_DIR}/${version}/batch_beam_search_online.py.patch

###
if [ $mode = "check" ]; then
  ls -l ${beamsearch_target}
  ls -l ${batchbeamsearch_target}
  ls -l ${batchbeamsearchonline_target}
fi

### install
if [ $mode = "install" ]; then
  ### for beam_search.py
  if [ ! -e ${beamsearch_target}.orig ]; then
    echo "  apply patch: " ${beamsearch_target} " " ${beamsearch_patch}
    patch -b ${beamsearch_target} ${beamsearch_patch}
  fi

  ### for batch_beam_search.py
  if [ ! -e ${batchbeamsearch_target}.orig ]; then
    echo "  apply patch: " ${batchbeamsearch_target} "->" ${batchbeamsearch_patch}
    patch -b ${batchbeamsearch_target} ${batchbeamsearch_patch}
  fi

  ### for batch_beam_search.py
  if [ ! -e ${batchbeamsearchonline_target}.orig ]; then
    echo "  apply patch: " ${batchbeamsearchonline_target} "->" ${batchbeamsearchonline_patch}
    patch -b ${batchbeamsearchonline_target} ${batchbeamsearchonline_patch}
  fi

fi

### uninstall
if [ $mode = "uninstall" ]; then
  if [ -e ${beamsearch_target}.orig ]; then
    echo "  unapply patch: " ${beamsearch_target} " " ${beamsearch_patch}
    patch -R ${beamsearch_target} ${beamsearch_patch}
    rm ${beamsearch_target}.orig
  fi
  if [ -e ${batchbeamsearch_target}.orig ]; then
    echo "  unapply patch: " ${batchbeamsearch_target} " " ${batchbeamsearch_patch}
    patch -R ${batchbeamsearch_target} ${batchbeamsearch_patch}
    rm ${batchbeamsearch_target}.orig
  fi
  if [ -e ${batchbeamsearchonline_target}.orig ]; then
    echo "  unapply patch: " ${batchbeamsearchonline_target} " " ${batchbeamsearchonline_patch}
    patch -R ${batchbeamsearchonline_target} ${batchbeamsearchonline_patch}
    rm ${batchbeamsearchonline_target}.orig
  fi

fi

