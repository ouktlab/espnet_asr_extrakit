###
if [ $# -ne 2 ]; then
    echo "usage: vis-file fst-header [plot]"
    exit
fi

###
visfile=$1
fstheader=$2
plot=$3

###
python3 auxtool/vis2fst.py ${visfile} ${fstheader}.fst ${fstheader}.sym
fstcompile ${fstheader}.fst \
    | fstdeterminize \
    | fstminimize \
    | fstrmepsilon \
    | fstarcsort \
	  > $fstheader.bin

###
fstprint \
    --isymbols=${fstheader}.sym \
    --osymbols=${fstheader}.sym \
    ${fstheader}.bin \
    > ${fstheader}.fst

###
if [ "${plot}" = "true" ]; then
  fstdraw --portrait \
	  --isymbols=$fstheader.sym \
          --osymbols=$fstheader.sym \
          $fstheader.bin \
    | dot -Tpdf > $fstheader.pdf
fi
