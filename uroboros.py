from argparse import ArgumentParser
from random import random
from collections import defaultdict
from sys import stdin
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s : " +
    "%(module)s (%(lineno)s) - %(levelname)s - %(message)s")


def parse_args():
    p = ArgumentParser()
    p.add_argument('-d', '--definitions', type=str, default="stdin")
    p.add_argument('-i', '--max-iter', type=int, default=10)
    p.add_argument(
        '-m', '--mode',
        choices=['rare', 'frequent', 'random', 'alpha', 'deflen', 'invdeflen'],
        default='rare',
        help="Skip most frequent/rare words or choose random words to skip")
    p.add_argument('-e', '--error-fn', type=str, default="errors")
    return p.parse_args()


def read_definition_graph(stream):
    #graph = defaultdict(set)
    graph = {}
    for l in stream:
        fs = l.decode('utf8').strip().split('\t')
        word = fs[0]
        if not word in graph:
            graph[word] = set()
        graph[word] |= set(fs[1:])
    for word, def_words in graph.iteritems():
        def_words -= set([word])
    return graph


def get_freqs(graph, mode):
    freqs = defaultdict(int)
    for def_w, definition in graph.iteritems():
        if 'len' in mode:
            freqs[def_w] = len(definition)
        else:
            freqs[def_w] += 1
            for word in definition:
                freqs[word] += 1
    return freqs


def create_uroboros(graph, mode, max_iter, freqs):
    sort_by = get_sort_mode(mode)
    for i in xrange(max_iter):
        logging.info('iter {0} -- graph size: {1}'.format(i + 1, len(graph)))
        size = len(graph)
        freqs = get_freqs(graph, mode)
        skip = collect_skip(graph, freqs, sort_by)
        for word, _ in sorted(freqs.iteritems(), key=sort_by):
            new_def = graph[word].copy()
            for def_w in graph[word]:
                if def_w in skip:
                    new_def |= skip[def_w]
                    new_def -= set([def_w])
            graph[word] = new_def
            if word in skip and not word in graph[word]:
                skip[word] = graph[word].copy()
                del graph[word]
                continue
            # updating definition
            new_def = graph[word].copy()
            for def_w in graph[word]:
                if def_w in skip:
                    new_def |= skip[def_w]
                    new_def -= set([def_w])
            graph[word] = new_def
        if len(graph) == size:
            logging.info('convergion reached at iter {0}'.format(i + 1))
            break
    return graph


def get_sort_mode(mode):
    if mode == 'random':
        sort_by = lambda x: random()
    elif mode == 'rare':
        sort_by = lambda x: x[1]
    elif mode == 'frequent':
        sort_by = lambda x: -x[1]
    elif mode == 'alpha':
        sort_by = lambda x: x[0]
    elif mode == 'deflen':
        sort_by = lambda x: (x[1])
    elif mode == 'invdeflen':
        sort_by = lambda x: -(x[1])
    return sort_by


def collect_skip(graph, freqs, sort_by):
    skip = {}
    skip_set = set()
    keep_left = set()
    skip_def_words = set()
    for word, _ in sorted(freqs.iteritems(), key=sort_by):
        def_words = graph[word]
        if def_words & skip_set or word in def_words or word in skip_def_words:
            keep_left.add(word)
            continue
        skip[word] = def_words
        skip_set.add(word)
        skip_def_words |= def_words
        #skip_set |= def_words
    logging.info('Collected {0} words to replace'.format(len(skip)))
    return skip


def skip_words(graph, to_skip):
    for word, right_side in graph.iteritems():
        new_rs = right_side.copy()
        for w2 in to_skip & right_side:
            new_rs |= graph[w2]
            new_rs -= set([w2])
        if new_rs:
            right_side = new_rs
    for word in to_skip:
        del graph[word]


def correct_integrity(graph, error_fn):
    missing = set()
    for words in graph.itervalues():
        for w in words:
            if not w in graph:
                missing.add(w)
        #missing |= set([w for w in words if not w in graph])
    with open(error_fn, 'w') as f:
        f.write("\n".join(sorted(missing)).encode('utf8'))
    for definition in graph.itervalues():
        definition -= missing


def main():
    args = parse_args()
    logging.info('reading definition graph...')
    if args.definitions == "stdin":
        def_graph = read_definition_graph(stdin)
    else:
        def_graph = read_definition_graph(args.definitions)
    logging.info('Definition graph read')
    correct_integrity(def_graph, args.error_fn)
    logging.info('Definition integrity corrected')
    freq = get_freqs(def_graph, args.mode)
    create_uroboros(def_graph, mode=args.mode, max_iter=args.max_iter,
                    freqs=freq)
    for word, right_side in def_graph.iteritems():
        print(u'{0}\t{1}'.format(
            word, '\t'.join(sorted(right_side))).encode('utf8'))

if __name__ == '__main__':
    main()
