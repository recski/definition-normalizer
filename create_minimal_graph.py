#!/usr/bin/env python2.7
from sys import stderr
from os import path
from collections import defaultdict
from argparse import ArgumentParser
import string
import re
from random import shuffle

word_re = re.compile(ur'^[A-Za-z\-\'\u2019\u00e9]+$', re.UNICODE)
punct = set(string.punctuation)
punct.remove('-')
punct.remove('\'')
shortened = set(['s', 't', 'll', 'm', 're', 'nt'])

class Log(object):
    def __init__(self, loglevel=1):
        self.loglevel = loglevel
        self.stat = defaultdict(int)
        self.replaced = list()

    def log_msg(self, msg):
        if self.loglevel > 0:
            stderr.write(msg.encode('utf8') + '\n')

myLog = Log(1)

def read_manual_mapping(map_fn):
    mapping = dict()
    f = open(map_fn)
    for l in f:
        fd = l.decode('utf8').strip().split('\t')
        if len(fd) < 2:
            stderr.write('Error in mapping file: ' + l + '\n')
            continue
        mapping[fd[0].strip()] = fd[1].strip()
    f.close()
    return mapping

def check_defs(defs, manual_mapping):
    ok = set()
    undef = set()
    for dm, ds_l in defs.iteritems():
        for ds in ds_l:
            for t in ds:
                if not t in defs and not t in manual_mapping \
                   and not t.lower() in defs and not t.lower() and not \
                   t.lower() in manual_mapping:
                    undef.add(t)
                else:
                    ok.add(t)
    return ok, undef

def write_defs(defs, fn):
    f = open(fn, 'w')
    for dm, ds_l in sorted(defs.iteritems(), key=lambda x: x[0]):
        for ds in ds_l:
            f.write('{0}\t{1}\n'.format(dm.encode('utf8'), '\t'.join(ds).encode('utf8')))
    f.close()

def count_freqs(defs, skip=None):
    freqs = defaultdict(int)
    for _, ds in defs.iteritems():
        for def_ in ds:
            for t in def_:
                if skip and t in skip:
                    continue
                freqs[t] += 1
    return freqs

def write_freqs_to_file(freqs, fn):
    f = open(fn, 'w')
    for v, k in sorted([(v_, k_) for k_, v_ in freqs.iteritems()]):
        f.write((str(v) + '\t' + k + '\n').encode('utf8'))
    f.close()

def reduce_definitions(defs, freqs, not_defined, threshold=1):
    replaced = set()
    blocking = defaultdict(list)
    print "defs len in reduce definitions: ", len(defs)
    #for dm, ds_l in sorted(defs.iteritems(), 
                           #key=lambda x: -freqs[x[0]]):
    rand = [i for i in defs.iteritems()]
    shuffle(rand)
    for dm, ds_l in rand:
        canBeReduced = True
        for ds in ds_l:
            for t in ds:
                #if t in not_defined:
                    #print t.encode('utf8')
                    #continue
                if not t in defs:
                    #print t.encode('utf8')
                    blocking[dm].append(t)
                    continue
                if t == dm or t in replaced:
                    canBeReduced = False
                    blocking[dm].append(t)
        if canBeReduced == True:
            replaced.add(dm)
            #myLog.replaced.append(dm)
    return replaced, blocking

def reduce_iter(defs, freqs, mapping, not_defined, cfg):
    iterations = cfg.iter_no
    this_defs = deep_copy_defs(defs)
    this_freqs = deep_copy_freqs(freqs)
    repl = set()
    prev_freqs = None
    for i in range(iterations):
        if len(this_freqs) == 0:
            break
        prev_freqs = deep_copy_freqs(this_freqs)
        print i+1, "iteration"
        repl, blocking = reduce_definitions(this_defs, this_freqs, not_defined, not_defined)
        prev_defs = deep_copy_defs(this_defs)
        this_freqs = count_freqs(this_defs, repl)
        if prev_freqs and len(prev_freqs) == len(this_freqs):
            break
        this_defs = remove_replaced_from_defs(prev_defs, repl)
        print len(this_freqs)
        write_defs(this_defs, cfg.iter_def_prefix + str(i+1))
        write_freqs_to_file(this_freqs, cfg.iter_freq_prefix + str(i+1))
        write_blocking(blocking, cfg.iter_blocking_prefix + str(i+1))
        write_replaced(repl, cfg.iter_replaced_prefix + str(i+1))
    return this_freqs, this_defs

def write_replaced(repl, fn):
    f = open(fn, 'w')
    f.write('\n'.join(repl).encode("utf8"))
    f.close()

def write_blocking(blocking, fn):
    f = open(fn, 'w')
    for w, bl in blocking.iteritems():
        f.write('{0}\t{1}\n'.format(w.encode('utf8'),
                                    ','.join(set(bl)).encode('utf8')))
    f.close()

def remove_replaced_from_defs(defs, repl):
    defs_new = dict()
    for k, v in defs.iteritems():
        if not k in repl:
            defs_new[k] = list()
            for def_ in v:
                defs_new[k].append(set())
                for word in def_:
                    if word in repl:
                        for repl_def in defs[word]:
                            defs_new[k][-1] |= repl_def - repl
                            if word in repl_def:
                                defs_new[k][-1].add(word)
                    else:
                        defs_new[k][-1].add(word)
    return defs_new

def deep_copy_freqs(f1):
    f2 = defaultdict(int)
    for k, v in f1.iteritems():
        f2[k] = v
    return f2

def deep_copy_defs(d1):
    d2 = dict()
    for dm, ds_l in d1.iteritems():
        d2[dm] = list()
        for ds in ds_l:
            d2[dm].append(set(ds))
    return d2

def read_defs_simple(fn, ignore=None):
    defs = defaultdict(list)
    f = open(fn)
    for l in f:
        fd = l.decode('utf8').strip().split('\t')
        if len(fd) < 2:
            continue
        defs[fd[0]].append(set())
        for w in fd[1:]:
            if not w in ignore and not w == fd[0]:
                defs[fd[0]][-1].add(w)
    f.close()
    return defs

def setup_parser():
    parser = ArgumentParser()
    parser.add_argument('-u', '--undefined-map', dest='undefined_map', type=str,
                       default='undefined_map')
    parser.add_argument('-n', '--write-not-defined', dest='not_defined', type=str,
                       default='not_defined')
    parser.add_argument('-d', '--normalized-definitions', dest='normalized_def', type=str,
                       default='definitions.normalized')
    parser.add_argument('--final-definitions', dest='final_def', type=str,
                       default='definitions.final')
    parser.add_argument('--freqs-orig', dest='freqs_orig', type=str,
                       help='write original frequencies to file',
                       default='freqs/freqs.orig')
    parser.add_argument('--freqs-reduced', dest='freqs_reduced', type=str,
                       help='write final, reduced frequencies to file',
                       default='freqs/freqs.reduced')
    parser.add_argument('--iter-def-prefix', dest='iter_def_prefix', type=str,
                       default='iter/def.')
    parser.add_argument('--iter-freq-prefix', dest='iter_freq_prefix', type=str,
                       default='iter/freq.')
    parser.add_argument('--iter-blocking-prefix', dest='iter_blocking_prefix', type=str,
                       default='iter/blocking.')
    parser.add_argument('--iter-replaced-prefix', dest='iter_replaced_prefix', type=str,
                       default='iter/replaced.')

    #TODO implement full normalization
    parser.add_argument('-f', '--fully-normalized-definitions', dest='fully_normalized_def', type=str,
                       default='definitions.full_normalized', 
                        help='output file for fully normalized definitions')
    parser.add_argument('--normalize', dest='normalize', action='store_true', default=False,
                       help='try to normalize definitions')
    parser.add_argument('--lower', dest='lower', action='store_true', default=False,
                       help='not used yet')
    parser.add_argument('-i', '--iter', dest='iter_no', default=5, type=int)

    return parser

def main():
    parser = setup_parser()
    cfg = parser.parse_args()

    if path.exists(cfg.undefined_map):
        mapping = read_manual_mapping(cfg.undefined_map)
    else:
        mapping = dict()
    if path.exists(cfg.not_defined):
        f = open(cfg.not_defined)
        undef = set([l.decode('utf8').strip() for l in f])
        f.close()
    else:
        undef = set()

    defs_exact = read_defs_simple(cfg.normalized_def, undef)
    #ok, und = check_defs(defs_exact, mapping)
    #write_defs(defs_exact, 'definitions.fully_normalized')
    #return
    freqs = count_freqs(defs_exact)
    write_freqs_to_file(freqs, cfg.freqs_orig)
    new_freqs, def_remain = reduce_iter(defs_exact, freqs, mapping, undef, cfg)
    write_freqs_to_file(new_freqs, cfg.freqs_reduced)
    write_defs(def_remain, cfg.final_def)

if __name__ == '__main__':
    main()

