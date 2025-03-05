###
if [ $# -le 1 ]; then
    echo "usage: txtfst optfst"
    exit
fi

txtfst=$1
optfst=$2

cat ${txtfst} | awk '{print $3 "\n" $4}' \
  | grep -v '^$' \
  | sort \
  | uniq \
  | awk '{print $1 " " NR - 1}' \
	> ${txtfst}.sym

fstcompile --isymbols=${txtfst}.sym --osymbols=${txtfst}.sym ${txtfst} \
  | fstdeterminize \
  | fstminimize \
  | fstrmepsilon \
  | fstarcsort \
  | fstprint --isymbols=${txtfst}.sym --osymbols=${txtfst}.sym  \
	     > ${optfst}

rm ${txtfst}.sym

