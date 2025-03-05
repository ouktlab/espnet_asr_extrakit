"""Sequential implementation of WFST-based Language Model."""
from typing import Any, Tuple, Union

import math
import queue
import pickle
import time
import array
import copy
from collections import defaultdict

import torch
import torch.nn as nn
from typeguard import typechecked
from espnet2.lm.abs_model import AbsLM

"""LM-level Hypothesis class
"""
class Hypothesis:
    """
    node: ID of state (WFST node)
    score: weight of WFST
    osyms: output symbols on WFST search path. <eps> is also included.
    depth: depth pruning
    """
    def __init__(self, node=0, score=0.0, osyms=[], depth=0, wildcard=2, in_any=False):
        self.node = node
        self.score = score
        self.osyms = osyms
        self.depth = depth
        self.wildcard = wildcard
        self.in_any = in_any

    def __str__(self):
        return f'node:{self.node:d}, score:{self.score:f}, osyms:{self.osyms}'

"""WFST network class
"""
class WFSTnetwork:
    """Node class
    used only in WFSTnetwork class
    """
    class Node:
        def __init__(self, idx, n):
            self.b = idx * 4
            self.e = (idx + n) * 4

    """
    """
    def __init__(self, token_list, ID_EPS=-1, W_SCALE=1.0e4, MIN_LOGP=-1.0e10):
        # for WFST data
        self.arcs = array.array('l', [])
        self.nodes = []
        
        # definition of tokens in ESPnet. It is idential to WFST isym.
        self.vocab_size = len(token_list)
        self.id2isym = token_list
        self.isym2id = {}
        for i, value in enumerate(token_list):
            self.isym2id[value] = i

        # table of transition prob.
        self.trans_lprob = None

        # dictionary for WFST osym
        self.osym2id = {}
        self.id2osym = []

        # 
        self.any_node = set()
        
        # const
        self.ID_EPS = ID_EPS
        self.ID_SOSEOS = self.isym2id['<sos/eos>']
        self.W_SCALE = W_SCALE
        self.MIN_LOGP = MIN_LOGP
        self.isym2id['<eps>'] = self.ID_EPS

    def clear(self):
        # for WFST data
        self.arcs = array.array('l', [])
        self.nodes = []
        self.any_node = set()
        
        self.trans_lprob = None

        self.osym2id = {}
        self.id2osym = []
        
    def convert(self):
        self.arcs = self.arcs.tolist()

    def reload(self, filename):
        print('[LOG]: reloading wfst text file...', filename)
        self.clear()
        self.load(filename)
        self.convert()

    # read WFST file in openFST text format
    def load(self, filename):        
        max_nodes = 0
        arc_counts = defaultdict(lambda: 0)
        
        print('[LOG]: now counting # of nodes of WFST...')
        with open(filename) as f:
            for line in f:
                tokens = line.strip().split()
                #
                src_node_id = int(tokens[0])
                if max_nodes < src_node_id:
                    max_nodes = src_node_id                                
                arc_counts[src_node_id] += 1                
                #
                if len(tokens) >= 4:
                    osym = tokens[3]
                    if self.osym2id.get(osym) is None:
                        self.osym2id[osym] = len(self.id2osym)
                        self.id2osym.append(osym)

        if self.osym2id.get('<eps>') is None:
            self.osym2id['<eps>'] = len(self.id2osym)
            self.id2osym.append('<eps>')
        if self.osym2id.get('<sos/eos>') is None:
            self.osym2id['<sos/eos>'] = len(self.id2osym)
            self.id2osym.append('<sos/eos>')
                        
        # memory allocation
        max_nodes += 1
        max_arcs = 0
        self.nodes = [None] * max_nodes
        for i in range(max_nodes):
            self.nodes[i] = self.Node(max_arcs, arc_counts[i])
            max_arcs += arc_counts[i]
        self.trans_lprob = torch.ones((max_nodes, self.vocab_size)) * self.MIN_LOGP

        #
        import re
        p_match = re.compile(r'\[(any.*|/any.*)\]')

        print('[LOG]: now creating wfst network ...')
        # 
        with open(filename) as f:
            n_arcs = 0
            for line in f:
                tokens = line.strip().split()                
                #
                n_arcs += 1                
                print(f'\r[LOG]: {n_arcs:d}/{max_arcs:d}', end='', flush=True)
                # 
                if len(tokens) == 1:
                    src_node_id = int(tokens[0])
                    dst_node_id = src_node_id
                    isym_id = self.isym2id['<sos/eos>']
                    osym_id = self.osym2id['<sos/eos>']
                    weight = 0
                else:
                    src_node_id = int(tokens[0])
                    dst_node_id = int(tokens[1])
                    if p_match.match(tokens[2]):
                        self.any_node.add(dst_node_id)
                        tokens[2] = '<eps>'
                    try:
                        isym_id = self.isym2id[tokens[2]]
                    except KeyError:
                        print(f'[ERROR]: the input symbol, {tokens[2]}, is not included in the ASR token set.')
                        print(f'[ERROR]: ABORT')
                        quit()
                    osym_id = self.osym2id[tokens[3]]
                    weight = 0 if len(tokens) < 5 else -float(tokens[4]) * self.W_SCALE / math.log10(math.e)

                #
                self.arcs.fromlist([dst_node_id, int(weight), isym_id, osym_id])                
                #
                if isym_id != self.ID_EPS:
                    self.trans_lprob[src_node_id, isym_id] = weight / self.W_SCALE

        print('')
        print(f'[LOG]: WFST stats:  # of nodes: {max_nodes:d}, # of isym: {len(self.id2isym):d}, # of osym: {len(self.id2osym):d}')

    # Pre-search isymbol probs for next symbol prediction
    def search_isym_lprob_hyp(self, hypset, max_depth=4):
        cum_lprob = torch.ones((self.vocab_size)) * self.MIN_LOGP

        hyps = queue.Queue()
        for h in hypset:
            hyps.put(Hypothesis(h.node))

        while not hyps.empty():
            hyp = hyps.get()            
            if hyp.depth > max_depth:
                print('[CAUTION]: reach max_depth')
                continue
            
            node = self.nodes[hyp.node]
            for n in range(node.b, node.e, 4):
                if self.arcs[n+2] == self.ID_EPS:
                    hyps.put(Hypothesis(self.arcs[n], hyp.score + self.arcs[n+1], depth=hyp.depth+1))
            lprob = self.trans_lprob[hyp.node,:] + hyp.score / self.W_SCALE            

            ## marginalization
            #cum_lprob = torch.log(torch.exp(lprob) + torch.exp(cum_lprob))
            ## max
            cum_lprob = torch.max(lprob, cum_lprob)

        return cum_lprob

    # Search actual path and update states
    def search_dst_node_hyp(self, hypset, actual_isym_id, max_depth=4, thres=50000.0, max_hyps=15):
        hyps = queue.Queue()
        for h in hypset:
            hyps.put(Hypothesis(h.node, h.score, h.osyms, wildcard=h.wildcard, in_any=h.in_any))

        newset = []
        max_score = -1.0e10
        while not hyps.empty():
            hyp = hyps.get()
            if hyp.depth > max_depth:
                print('[CAUTION]: reach max_depth')
                continue
            
            node = self.nodes[hyp.node]
            for n in range(node.b, node.e, 4):
                if self.arcs[n+2] == self.ID_EPS:
                    in_any = not hyp.in_any if self.arcs[n] in self.any_node else hyp.in_any
                    hyps.put(Hypothesis(self.arcs[n], hyp.score + self.arcs[n+1],
                                        hyp.osyms + [self.id2osym[self.arcs[n+3]]], hyp.depth+1, wildcard=hyp.wildcard, in_any=in_any))
                elif self.arcs[n+2] == actual_isym_id:
                    in_any = not hyp.in_any if self.arcs[n] in self.any_node else hyp.in_any
                    h = Hypothesis(self.arcs[n], hyp.score + self.arcs[n+1],
                                   hyp.osyms + [self.id2osym[self.arcs[n+3]]], wildcard=hyp.wildcard, in_any=in_any)
                    max_score = h.score if max_score < h.score else max_score
                    newset.append(h)
        
        # local beam search
        newset = sorted(newset, key=lambda x: x.score, reverse=True)
        #diff_scores = []
        for i, x in enumerate(newset):
            #diff_scores.append(max_score - x.score)
            if max_score - x.score > thres or i >= max_hyps:
                max_hyps = i
                break

        # for in-any hypotheses restriction
        inany = True
        for i, x in enumerate(newset[:max_hyps]):
            if x.in_any is False:
                inany = False

        return max_score/self.W_SCALE, inany, newset[:max_hyps]
    
    def finalize_hyp(self, hypset, max_depth=4, thres=200000.0, max_hyps=10):
        max_score, inany, newhypset = self.search_dst_node_hyp(hypset, self.ID_SOSEOS, max_depth, thres, max_hyps)
        return max_score, newhypset

    def shrink_osyms(self, osyms):
        shrinked = []
        for x in osyms:
            if x == '<eps>':
                continue
            if x == '<sos/eos>':
                continue
            shrinked.append(x)
        return shrinked


class WFSTLM(AbsLM):
    """WFSTLM.

    """
    @typechecked
    def __init__(
        self,
        vocab_size: int,
        wfst_file: str | None,
        token_list: Any,
        max_depth: int = 4,
        thres: float = 10000.0,
        max_hyps: int = 15,
        max_any_cnt: int = 1,
    ):
        super().__init__()

        if len(token_list) != vocab_size:
            print(f'[ERROR]: WFSTLM: the length of the token_list {len(token_list):d} is not equal to the vocab_size {vocab_size:d}')
            quit()
        
        self.vocab_size = vocab_size
        self.LOG_ZERO = torch.ones(vocab_size) * -1.0e10

        self.max_depth = max_depth
        self.thres = thres
        self.max_hyps = max_hyps

        self.max_any_cnt = max_any_cnt

        if wfst_file is None:
            print('[CAUTION]: wfst_file was not specified. Load only wfstnetwork class.')
            self.wfst = WFSTnetwork(token_list)
        elif '.txt' in wfst_file:
            print('[LOG]: now loading wfst text file...')
            self.wfst = WFSTnetwork(token_list)
            self.wfst.load(wfst_file)
            print('[LOG]: finish loading wfst text file...')
            self.wfst.convert()
        elif '.bin' in wfst_file:
            time_s = time.perf_counter()
            print('[LOG]: now loading wfst binary file...')
            with open(wfst_file, 'rb') as f:
                self.wfst = pickle.load(f)
            time_m = time.perf_counter()
            print(f'[LOG]: finish reading file {time_m-time_s:f}')
            print(f'[LOG]: now converting data into internal format...')
            self.wfst.convert()
            time_e = time.perf_counter()
            print(f'[LOG]: finish converting data {time_e-time_m:f}')
        else:
            print('[CAUTION]: wfst_file is not .txt or .bin. Load only wfstnetwork class.')
            self.wfst = WFSTnetwork(token_list)
        
        ##
        print('[LOG]: WFSTLM: ', self.vocab_size, wfst_file, self.max_depth, self.thres, self.max_hyps)

    def forward(
        self, input: torch.Tensor, hidden: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """ Never used.
        """
        return (
            None,
            None,
        )

    def score(self, y: torch.Tensor, state: Any, x: torch.Tensor) -> Tuple[torch.Tensor, Any]:
        """Score new token.
        Args:
            y: 1D torch.int64 prefix tokens.
            state: Scorer state for prefix tokens
            x: 2D encoder feature that generates ys.

        Returns:
            Tuple of
                torch.float32 scores for next token (n_vocab)
                and next state for ys

        """
        y, new_state = self.batch_score(y[-1].view(1, 1), state, x)
        logp = y.log_softmax(dim=-1).view(-1)
        return logp, new_state

    def batch_score(
        self, ys: torch.Tensor, states: Any, xs: torch.Tensor
    ) -> Tuple[torch.Tensor, Any]:
        """Score new token batch.

        Args:
            ys (torch.Tensor): torch.int64 prefix tokens (n_batch, ylen).
            states (List[Any]): Scorer states for prefix tokens.
            xs (torch.Tensor):
                The encoder feature that generates ys (n_batch, xlen, n_feat).

        Returns:
            tuple[torch.Tensor, List[Any]]: Tuple of
                batchfied scores for next token with shape of `(n_batch, n_vocab)`
                and next state list for ys.

        """
        # set initial state
        if states[0] is None:
            states = [{'score':0, 'isyms':[], 'hypset':[Hypothesis()]}]

        newstates = []
        cnt_any = 0

        #time_s = time.perf_counter()
        for i, x in enumerate(states):
            actual_isym_id = ys[i][-1].item()
            max_score, inany, newset = self.wfst.search_dst_node_hyp(x['hypset'], actual_isym_id,
                                                                     max_depth=self.max_depth,
                                                                     thres=self.thres, max_hyps=self.max_hyps)            
            deadend = True if cnt_any >= self.max_any_cnt and inany is True else False
            cnt_any = cnt_any + 1 if inany is True else cnt_any
            newstates.append({'score':max_score, 'isyms':x['isyms'] + [self.wfst.id2isym[actual_isym_id]],
                              'hypset':newset, 'deadend':deadend})
            
        logp = torch.zeros(ys.shape[0], self.vocab_size)
        for i, x in enumerate(newstates):
            logp[i,:] = self.LOG_ZERO if x['deadend'] else self.wfst.search_isym_lprob_hyp(x['hypset'], max_depth=self.max_depth)
        
        return logp.to(ys.device), newstates

# 
if __name__ == '__main__':
    pass

