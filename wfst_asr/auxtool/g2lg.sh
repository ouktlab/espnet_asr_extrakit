###
if [ $# -le 5 ]; then
    echo "usage: fstGbin symG fstLtxt fstLbin symL fstLGtxt [minimize]"
    exit
fi

## in ##
fstGbin=$1
symG=$2
## out ###
fstLtxt=$3
fstLbin=$4
symL=$5
fstLGtxt=$6
minimize=$7

##
fstprint --isymbols=${symG} --osymbols=${symG} ${fstGbin} \
  | python3 auxtool/fst2l.py ${symL} --use_pron \
	    > ${fstLtxt}

##
sh auxtool/txtfst2binfst.sh \
   ${fstLtxt} \
   ${fstLbin} \
   ${symL} \
   ${symG}

##
if [ "$minimize" = "true" ]; then
  fstcompose ${fstLbin} ${fstGbin} \
    | fstdeterminize \
    | fstminimize \
    | fstrmepsilon \
    | fstarcsort \
    | fstprint --isymbols=${symL} --osymbols=${symG} \
	       > ${fstLGtxt}
else
  fstcompose ${fstLbin} ${fstGbin} \
    | fstdeterminize \
    | fstrmepsilon \
    | fstarcsort \
    | fstprint --isymbols=${symL} --osymbols=${symG} \
	       > ${fstLGtxt}
fi
