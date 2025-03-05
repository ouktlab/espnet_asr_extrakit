###
stage=0

###
#
###
if [ $stage -le 0 ]; then
  # conver vis into fst
  sh auxtool/vis2fst.sh tmpl_vis/net_railroad.vis \
     fst_model/railroad_G
  sh auxtool/vis2fst.sh tmpl_vis/net_station.vis \
     fst_model/station_G

  # generate global symbol table for replacement
  cat fst_model/railroad_G.sym fst_model/station_G.sym | sort -k 2 -n | uniq \
    | awk '{print $1 " " NR-1} END{print "@main " NR}' \
	  > fst_model/railroad_station_G.sym

  # generate binary fst
  sh auxtool/txtfst2binfst.sh \
     fst_model/railroad_G.fst \
     fst_model/railroad_G.bin \
     fst_model/railroad_station_G.sym \
     fst_model/railroad_station_G.sym

  sh auxtool/txtfst2binfst.sh \
     fst_model/station_G.fst \
     fst_model/station_G.bin \
     fst_model/railroad_station_G.sym \
     fst_model/railroad_station_G.sym \
     true
  
  # replace fst
  mainid=`grep "\@main" fst_model/railroad_station_G.sym  | awk '{print $2}'`
  stationid=`grep "\@station" fst_model/railroad_station_G.sym  | awk '{print $2}'`

  # 
  fstreplace --epsilon_on_replace fst_model/railroad_G.bin ${mainid} fst_model/station_G.bin ${stationid} \
    | fstdeterminize \
    | fstminimize \
    | fstrmepsilon \
    | fstarcsort \
    | fstprint --isymbols=fst_model/railroad_station_G.sym --osymbols=fst_model/railroad_station_G.sym \
	       > fst_model/railroad_station_G.fst
    
  sh auxtool/txtfst2binfst.sh \
     fst_model/railroad_station_G.fst \
     fst_model/railroad_station_G.bin \
     fst_model/railroad_station_G.sym \
     fst_model/railroad_station_G.sym

  sh auxtool/g2lg.sh fst_model/railroad_station_G.bin fst_model/railroad_station_G.sym \
     fst_model/railroad_station_L.fst fst_model/railroad_station_L.bin \
     fst_model/railroad_station_L.sym fst_model/railroad_station_LG.fst true

  ## 
  cat fst_model/railroad_station_LG.fst | python3 auxtool/rmtag.py --use_char \
	      > fst_model/railroad_station_LG_rmtag.fst
  
  sh auxtool/optfst.sh fst_model/railroad_station_LG_rmtag.fst fst_model/railroad_station_final.fst

  rm fst_model/railroad_G.*
  rm fst_model/station_G.*
  rm fst_model/railroad_station_G.*
  rm fst_model/railroad_station_L.*
  rm fst_model/railroad_station_LG.*
  rm fst_model/railroad_station_LG_rmtag.*

fi

###
#
###
if [ $stage -le 1 ]; then
  ###
  cat tmpl_fst/list_any_token.txt \
    | python3 auxtool/tokenlist2owfst.py \
	      > fst_model/any_single.fst

  # generate global symbol table for replacement
  cat fst_model/any_single.fst tmpl_fst/any_tmpl_len2-15.fst \
    | awk '{print $3 "\n" $4}' \
    | grep -v "<eps>" \
    | grep -v '^$' \
    | sort | uniq \
    | awk 'BEGIN{print "<eps> 0"} {print $1 " " NR} END{print "@main " NR+1}' \
	  > fst_model/any_len2-15_G.sym

  # generate binary fst
  sh auxtool/txtfst2binfst.sh \
     fst_model/any_single.fst \
     fst_model/any_single.bin \
     fst_model/any_len2-15_G.sym \
     fst_model/any_len2-15_G.sym

  sh auxtool/txtfst2binfst.sh \
     tmpl_fst/any_tmpl_len2-15.fst \
     fst_model/any_tmpl_len2-15.bin \
     fst_model/any_len2-15_G.sym \
     fst_model/any_len2-15_G.sym

  # replace fst
  mainid=`grep "\@main" fst_model/any_len2-15_G.sym  | awk '{print $2}'`
  singleanyid=`grep "\@singleany" fst_model/any_len2-15_G.sym  | awk '{print $2}'`

  #
  fstreplace --epsilon_on_replace fst_model/any_tmpl_len2-15.bin ${mainid} fst_model/any_single.bin ${singleanyid} \
    | fstdeterminize \
    | fstminimize \
    | fstrmepsilon \
    | fstarcsort \
    | fstprint --isymbols=fst_model/any_len2-15_G.sym --osymbols=fst_model/any_len2-15_G.sym \
	       > fst_model/any_len2-15_G.fst

fi

###
#
###
if [ $stage -le 2 ]; then
  # conver vis into fst
  sh auxtool/vis2fst.sh tmpl_vis/net_railroad.vis \
     fst_model/railroad_G

  # generate global symbol table for replacement
  cat fst_model/railroad_G.fst fst_model/any_len2-15_G.fst \
    | awk '{print $3 "\n" $4}' \
    | grep -v "<eps>" \
    | grep -v '^$' \
    | sort | uniq \
    | awk 'BEGIN{print "<eps> 0"} {print $1 " " NR} END{print "@main " NR+1}' \
	  > fst_model/railroad_any_G.sym
  
  # generate binary fst
  sh auxtool/txtfst2binfst.sh \
     fst_model/railroad_G.fst \
     fst_model/railroad_G.bin \
     fst_model/railroad_any_G.sym \
     fst_model/railroad_any_G.sym
  
  sh auxtool/txtfst2binfst.sh \
     fst_model/any_len2-15_G.fst \
     fst_model/any_len2-15_G.bin \
     fst_model/railroad_any_G.sym \
     fst_model/railroad_any_G.sym \
     true
  
  # replace fst
  mainid=`grep "\@main" fst_model/railroad_any_G.sym  | awk '{print $2}'`
  stationid=`grep "\@station" fst_model/railroad_any_G.sym  | awk '{print $2}'`
  #echo ${mainid} " " ${stationid}

  # 
  #  --epsilon_on_replace
  fstreplace --epsilon_on_replace fst_model/railroad_G.bin ${mainid} fst_model/any_len2-15_G.bin ${stationid} \
    | fstdeterminize \
    | fstminimize \
    | fstrmepsilon \
    | fstarcsort \
	> fst_model/railroad_any_G.bin
  
  fstprint --isymbols=fst_model/railroad_any_G.sym \
	   --osymbols=fst_model/railroad_any_G.sym \
	   fst_model/railroad_any_G.bin \
	   > fst_model/railroad_any_G.fst
  
  
  sh auxtool/g2lg.sh fst_model/railroad_any_G.bin fst_model/railroad_any_G.sym \
     fst_model/railroad_any_L.fst fst_model/railroad_any_L.bin \
     fst_model/railroad_any_L.sym fst_model/railroad_any_LG.fst true
  
  ## 
  cat fst_model/railroad_any_LG.fst | python3 auxtool/rmtag.py --use_char \
	      > fst_model/railroad_any_LG_rmtag.fst

  sh auxtool/rmepsfst.sh fst_model/railroad_any_LG_rmtag.fst fst_model/railroad_any_final.fst
  
  rm fst_model/railroad_G.*
  rm fst_model/railroad_any_G.*
  rm fst_model/railroad_any_L.*
  rm fst_model/railroad_any_LG.*
  rm fst_model/railroad_any_LG_rmtag.*

fi


if [ $stage -le 3 ]; then
  # conver vis into fst
  sh auxtool/vis2fst.sh tmpl_vis/net_name.vis \
     fst_model/name_G

  # generate global symbol table for replacement
  cat fst_model/name_G.fst fst_model/any_len2-15_G.fst \
    | awk '{print $3 "\n" $4}' \
    | grep -v "<eps>" \
    | grep -v '^$' \
    | sort | uniq \
    | awk 'BEGIN{print "<eps> 0"} {print $1 " " NR} END{print "@main " NR+1}' \
	  > fst_model/name_any_G.sym

  # generate binary fst
  sh auxtool/txtfst2binfst.sh \
     fst_model/name_G.fst \
     fst_model/name_G.bin \
     fst_model/name_any_G.sym \
     fst_model/name_any_G.sym
  
  sh auxtool/txtfst2binfst.sh \
     fst_model/any_len2-15_G.fst \
     fst_model/any_len2-15_G.bin \
     fst_model/name_any_G.sym \
     fst_model/name_any_G.sym \
     true


  # replace fst
  mainid=`grep "\@main" fst_model/name_any_G.sym  | awk '{print $2}'`
  myojiid=`grep "\@myoji" fst_model/name_any_G.sym  | awk '{print $2}'`
  namaeid=`grep "\@namae" fst_model/name_any_G.sym  | awk '{print $2}'`
  #echo ${mainid} " " ${myojiid}

  # 
  #  --epsilon_on_replace
  fstreplace --epsilon_on_replace fst_model/name_G.bin ${mainid} fst_model/any_len2-15_G.bin ${myojiid} fst_model/any_len2-15_G.bin ${namaeid} \
    | fstdeterminize \
    | fstminimize \
    | fstrmepsilon \
    | fstarcsort \
	> fst_model/name_any_G.bin
  
  fstprint --isymbols=fst_model/name_any_G.sym \
	   --osymbols=fst_model/name_any_G.sym \
	   fst_model/name_any_G.bin \
	   > fst_model/name_any_G.fst  
  
  sh auxtool/g2lg.sh fst_model/name_any_G.bin fst_model/name_any_G.sym \
     fst_model/name_any_L.fst fst_model/name_any_L.bin \
     fst_model/name_any_L.sym fst_model/name_any_LG.fst true
  
  ## 
  cat fst_model/name_any_LG.fst | python3 auxtool/rmtag.py --use_char \
	      > fst_model/name_any_LG_rmtag.fst

  sh auxtool/rmepsfst.sh fst_model/name_any_LG_rmtag.fst fst_model/name_any_final.fst
  
  rm fst_model/name_G.*
  rm fst_model/name_any_G.*
  rm fst_model/name_any_L.*
  rm fst_model/name_any_LG.*
  rm fst_model/name_any_LG_rmtag.*

fi
