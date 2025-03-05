import yaml
import pickle
from espnet2.lm.wfst_lm import WFSTnetwork

def parse():
    import argparse
    
    #
    parser = argparse.ArgumentParser(description='convert text fst-file to WFSTnetwork-class pickle file')

    parser.add_argument('asrconfig', help='yaml file for asr configuration [in]')
    parser.add_argument('wfstconfig', help='yaml file for wfst-lm configuration [out]')
    parser.add_argument('--textfile', help='text fst-file [in]')
    parser.add_argument('--pklfile', help='pickle file [out]')
    
    args = parser.parse_args()

    return args

def main():
    args = parse()

    textfile = args.textfile
    asrconfigfile = args.asrconfig
    wfstconfigfile = args.wfstconfig
    wfstbin = args.pklfile

    ###
    with open(asrconfigfile, 'r') as yml:
        asrconfig = yaml.safe_load(yml)

    ### default settings
    wfstconfig = {
        'init': None,
        'token_list': asrconfig['token_list'],
        'model_conf': {'ignore_id':0},
        'lm': 'wfst',
    }
    wfstconfig['lm_conf'] = {
        'max_hyps': 10,
        'max_any_cnt': 3,
        'wfst_file': wfstbin,
        'token_list': wfstconfig['token_list']
    }
    
    ###
    with open(wfstconfigfile, mode='w', encoding='utf-8') as f:
        yaml.safe_dump(wfstconfig, f, allow_unicode=True)
        
    ###
    if textfile is not None and wfstbin is not None:
        wfstnet = WFSTnetwork(asrconfig['token_list'])
        wfstnet.load(textfile)
    
        with open(wfstbin, 'wb') as f:
            pickle.dump(wfstnet, f)

    
if __name__ == '__main__':
    main()
