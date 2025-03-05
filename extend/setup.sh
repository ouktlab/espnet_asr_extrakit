##
stage=0

##
install_wfst=true
uninstall_wfst=
install_md=true
uninstall_md=
install_cprob=true
uninstall_cprob=

##
version=ver2502
checkoutv=b57dd0418ab2f7a03a21239f70decb9837cb2b0f # for ver2502

#####################
if [ -n "${checkoutv}" ] && [ $stage -le 0 ]; then
  cd ../espnet/
  echo "git checkout ${checkoutv}"
  git checkout ${checkoutv}
  cd ../extend/
fi

######## WFST #######
##
if [ "${install_wfst}" =  "true" ] && [ $stage -le 2 ]; then
  echo "---- install WFSTLM ----"
  ../script/launcher sh install_wfstlm.sh ${version} install 
fi
##
if [ "${uninstall_wfst}" =  "true" ] && [ $stage -le 3 ]; then
  echo "---- uninstall WFSTLM ----"
  ../script/launcher sh install_wfstlm.sh ${version} uninstall
fi

######## CProb #######
##
if [ "${install_cprob}" =  "true" ] && [ $stage -le 3 ]; then
  echo "---- install cprob ----"
  ../script/launcher sh install_cprob.sh ${version} install 
fi
##
if [ "${uninstall_cprob}" =  "true" ] && [ $stage -le 4 ]; then
  echo "---- uninstall cprob ----"
  ../script/launcher sh install_cprob.sh ${version} uninstall
fi

######## MD #######
##
if [ "${install_md}" =  "true" ] && [ $stage -le 5 ]; then
  echo "---- install MD ----"
  ../script/launcher sh install_md.sh ${version} install 
fi
##
if [ "${uninstall_md}" =  "true" ] && [ $stage -le 6 ]; then
  echo "---- uninstall MD ----"
  ../script/launcher sh install_md.sh ${version} uninstall
fi
