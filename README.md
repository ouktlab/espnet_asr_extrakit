# Espnet ASR Extrakit #
This repository provides examples and modules using [ESPnet](https://github.com/espnet/espnet) ASR mainly for academic research and education (training).  
These examples and modules uses ESPnet toolkit, and patch files are sometimes applied to its source codes.  
Note that coding standars, error handling, comments and so on in this toolkit are not suitable for joint development.


## Features ##
- Simple examples for training or fine tuning ASR/LM model using local data
- Simple example for character error rate (CER)
- WFST LM module and examples for grammar-based or traditional n-gram-based model

## Requirements ##
ESPnet is required. Our toolkit uses python environment of ESPnet. 

- GPU environment
- espnet (source code + install)
- openfst/libfst-tools (for WFST LM)

Option: additional python libraries are required for simple grammar editor.
- tkinter
- eel

Python3.10 is suitable for installation of ESPnet (as of 2024/8).

## Installation and Preparation ##
Install ESPnet according to the instruction of ESPnet.
```
git clone https://github.com/espnet/espnet.git
cd espnet
cd tools
./setup_venv.sh $(command -v python3)
make
```

Copy and edit a "launcher" file.
```
cp script/launcher.tmpl script/launcher
emacs -nw script/launcher  
```
Set your ESPnet directory to the "__ESPNET_ROOT" variable. 
```
__ESPNET_ROOT=~/git/espnet_asr_extrakit/
```


Please use the shell script to setup environemnt automatically. It sometimes ask you to type your password for installations using "sudo apt".
```
sh setup.sh
```

If you want to enable WFST LM, please edit the "setup.sh" as
```
enable_wfst=true
```

## ASR training ###
### Preparation
Move to the working directory.
```
$ cd train_asr
```

All you need is to prepare 
 - audio files
 - their transcriptions 
 - list files

for ASR model training.

In this example, small amount of data is prepared in the "data/" directory. Note that more and more data are required for actual training or fine tuning.
```
$ ls data/audio/
ambig01.flac  data022.flac  data024.flac  data026.flac  data028.flac  name01.flac      railroad02.flac
data021.flac  data023.flac  data025.flac  data027.flac  data040.flac  railroad01.flac  railroad03.flac
```

The audio files are summarized as pairs of key and its file path in the "data/list/egs_train_key-path.txt".
```
$ cat data/list/egs_train_key-path.txt
spkr01-key_data021 data/audio/data021.flac
spkr01-key_data022 data/audio/data022.flac
spkr01-key_data023 data/audio/data023.flac
spkr01-key_data024 data/audio/data024.flac
spkr01-key_data025 data/audio/data025.flac
spkr01-key_data026 data/audio/data026.flac
spkr01-key_data027 data/audio/data027.flac
spkr01-key_data028 data/audio/data028.flac
```

Corresponding transcriptions are listed in the "data/list/egs_train_key-text.txt". We used text of Wikipedia for this example. 
```
$ cat data/list/egs_train_key-text.txt
spkr01-key_data021 音声認識は声がもつ情報をコンピュータに認識させるタスクの総称である
spkr01-key_data022 ヒトの音声認識と対比して自動音声認識とも呼ばれる
spkr01-key_data023 例として文字起こしや話者認識が挙げられる
spkr01-key_data024 音声認識は音声に含まれる情報を認識するタスクの総称であり具体的に解かれる問題の例として以下が挙げられる
spkr01-key_data025 音声認識をサブタスクとして含むタスクには以下が挙げられる
spkr01-key_data026 音声認識では統計的手法が良く用いられている
spkr01-key_data027 これは大量の発話を記録した学習用データから音声の特徴を蓄積し
spkr01-key_data028 認識対象となる入力音声から抽出した特徴と蓄積された特徴とを比較しながら
```

List files for validation are also prepared. 
```
$ ls data/list/egs_valid_key-*
data/list/egs_valid_key-path.txt  data/list/egs_valid_key-text.txt
```

If you want to use your own training data, the simplest way is to replace these files into your own files. 

### training from scratch ####
```
$ sh run.egs.scratch.sh
```

### fine tuning ####
```
$ sh run.egs.finetue.sh
```

## LM training ###
### Preparation ###
Move to the working directory.
```
$ cd train_lm
```

All you need is to prepare only
 - text file

for LM model training.

The format of the text file is the same as the transcription file used in the ASR model training. 
```
$ cat data/list/egs_train_key-text.txt
spkr01-key_data021 音声認識は声がもつ情報をコンピュータに認識させるタスクの総称である
spkr01-key_data022 ヒトの音声認識と対比して自動音声認識とも呼ばれる
spkr01-key_data023 例として文字起こしや話者認識が挙げられる
spkr01-key_data024 音声認識は音声に含まれる情報を認識するタスクの総称であり具体的に解かれる問題の例として以下が挙げられる
spkr01-key_data025 音声認識をサブタスクとして含むタスクには以下が挙げられる
spkr01-key_data026 音声認識では統計的手法が良く用いられている
spkr01-key_data027 これは大量の発話を記録した学習用データから音声の特徴を蓄積し
spkr01-key_data028 認識対象となる入力音声から抽出した特徴と蓄積された特徴とを比較しながら
```


Note that the **"token list" must be same between ASR and LM models**.   
**Be careful when you use a different text data from the transcription used in the ASR model training**. 

### training from scratch ####
```
sh run.egs.scratch.sh
```

### fine tuning ####
```
sh run.egs.finetue.sh
```

## WFST LM ###
### Preparation ###
Enable wfst in the "setup.sh" in the root directory of this toolkit.
```
$ emacs -nw setup.sh # edit option
$ sh setup.sh
$ . venv/bin/activate
```

Install WFST LM into ESPnet environment.
```
$ cd extend
$ sh setup.sh
$ cd ../
```

Move to working directory.
```
cd wfst_asr
```

### Run example shell
```
sh run.egs.asr.sh
```

### Simple Grammar Editor and WFST conversion
```
(venv) $ python3 auxtool/editor.py
```
<img src="img/fst_editor.png" width="600">



