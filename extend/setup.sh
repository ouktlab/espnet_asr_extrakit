##
install_wfst=true
uninstall_wfst=

version=ver2502
checkoutv=b57dd0418ab2f7a03a21239f70decb9837cb2b0f # for ver2502

#####################
if [ -n "${checkoutv}" ]; then
  cd ../espnet/
  echo "git checkout ${checkoutv}"
  exit;
fi

######## WFST #######
##
if [ "${install_wfst}" =  "true" ]; then
  echo "---- install WFSTLM ----"
  ../script/launcher sh install_wfstlm.sh install ${version}
fi
##
if [ "${uninstall_wfst}" =  "true" ]; then
  echo "---- uninstall WFSTLM ----"
  ../script/launcher sh install_wfstlm.sh uninstall ${version}
fi
