# -*- coding: utf-8 -*-
import argparse
import sys
import re

class Edge:
    def __init__(self, id_from, id_to):
        self.id_from = id_from
        self.id_to = id_to

    def print(self):
        print(self.n_id)

class Node:
    def __init__(self, sym_id, is_end):
        self.sym_id = sym_id
        self.is_end = is_end

def readVIS(vis):
    accept = []
    sym = {'<eps>':0}
    invsym = {0:'<eps>'}
    id2num = {}
    n_sym = 1

    nodes = {}
    edges = []

    state = 0
    n_id = 2
    with open(vis, 'r') as f:
        for line in f:
            if line.find('--edges--') > -1:
                state = 'edge'
                continue
            if line.find('--nodes--') > -1:
                state = 'node'
                continue

            token = line.strip().split(',')
            if state == 'edge':
                edges.append(Edge(token[0], token[1]))
                #print('edge: ' +  token[0] + ' ' + token[1])

            if state == 'node':
                if token[1] not in sym:
                    sym[token[1]] = n_sym
                    invsym[n_sym] = token[1]
                    n_sym = n_sym + 1

                if token[1] == '<s>':
                    id2num[token[0]] = 1

                if token[0] not in id2num:
                    id2num[token[0]] = n_id
                    n_id = n_id + 1

                if token[1] == '</s>':
                    is_end = True
                else:
                    is_end = False
                nodes[token[0]] = Node(sym[token[1]], is_end)
                #nodes[token[0]] = Node(token[1], is_end)

    #for x,y in enumerate(sym):
    #    print(str(y) + ' ' + str(x))
    '''
    print('0 1 <s> <s>')
    for x in edges:
        id_from = id2num[x.id_from]
        id_to = id2num[x.id_to]
        print(str(id_from) + ' ' + str(id_to)
            + ' ' + str(invsym[nodes[x.id_to].sym_id])
            + ' ' + str(invsym[nodes[x.id_to].sym_id]))
        #print(x.id_from + ' ' + x.id_to)
    '''
    #for x in nodes:
    #    print(str(x) + ' ' + str(nodes[x].sym_id))

    return [nodes, edges, sym, id2num]

def writeFST(fstfile, symfile, nodes, edges, sym, id2num):
    with open(fstfile, 'w') as f:
        print('0 1 ' + str(sym['<s>']) + ' ' + str(sym['<s>']), file=f)
        for x in edges:
            id_from = id2num[x.id_from]
            id_to = id2num[x.id_to]
            print(str(id_from) + ' ' + str(id_to)
                + ' ' + str(nodes[x.id_to].sym_id)
                + ' ' + str(nodes[x.id_to].sym_id), file=f)
            if nodes[x.id_to].is_end == True:
                print(str(id_to), file=f)

    with open(symfile, 'w') as f:
        for x,y in enumerate(sym):
            print(str(y) + ' ' + str(x), file=f)

# main
if __name__ == '__main__':

    # argument analysis
    parser = argparse.ArgumentParser(
                    description='Generate context dependent network.',
                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('vis', type=str, help='fst filename')
    parser.add_argument('fst', type=str, help='fst filename')
    parser.add_argument('sym', type=str, help='fst filename')
    args = parser.parse_args()

    # Lexicon のシンボルを読み込む
    [nodes, edges, sym, id2num] = readVIS(args.vis)
    writeFST(args.fst, args.sym, nodes, edges, sym, id2num)
