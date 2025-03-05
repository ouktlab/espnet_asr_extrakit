###
if [ $# -le 3 ]; then
    echo "usage: txtfst binfst isymbols osymbols [replace]"
    exit
fi

###
txtfst=$1
binfst=$2
isymbols=$3
osymbols=$4
replace=$5

###
if [ "$replace" = "true" ]; then
  cat ${txtfst} | sed -e 's|<s>|<eps>|g' | sed -e 's|</s>|<eps>|g' \
    | fstcompile --isymbols=${isymbols} --osymbols=${osymbols} \
    | fstdeterminize \
    | fstminimize \
    | fstrmepsilon \
    | fstarcsort \
	> ${binfst}
else  
  fstcompile --isymbols=${isymbols} --osymbols=${osymbols} ${txtfst} \
    | fstdeterminize \
    | fstminimize \
    | fstrmepsilon \
    | fstarcsort \
	> ${binfst}
  exit;
fi
