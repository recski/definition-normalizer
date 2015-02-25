#!/usr/bin/env python2.7
from sys import stdin, stdout
from argparse import ArgumentParser
import re

word_re = re.compile(ur'^[A-Za-z\-\'\u2019\u00e9]+$', re.UNICODE)

def setup_parser():
    parser = ArgumentParser()
    parser.add_argument('-s', '--separator', dest='sep', type=str,
                        default=' ', help='separator on right side')
    parser.add_argument('-l', '--lower', dest='lower', action='store_true',
                        default=False, help='lower all words')
    parser.add_argument('-e', '--encoding', dest='encoding', type=str,
                        default='utf8',
                        help='input encoding. Output is always UTF8')

    return parser

def tokenize_line(line, cfg):
    fd = line.split('\t')
    left = normalize_left(fd[0], cfg)
    right = '\t'.join(fd[1:])
    words = remove_spec(right, cfg).split(cfg.sep)
    words_norm = list()
    for w in words:
        w_ = normalize_word(w, cfg)
        if w_:
            words_norm.append(w_)
    return [left] + words_norm

def normalize_left(left, cfg):
    return left

def remove_spec(line, cfg):
    l = line.replace('.', '')
    l = l.replace(':', '')
    if cfg.lower:
        l = l.lower()
    return l

def normalize_word(word, cfg):
    if not word_re.match(word):
        return None
    return word

def main():
    parser = setup_parser()
    cfg = parser.parse_args()

    for l in stdin:
        tok = tokenize_line(l.strip().decode(cfg.encoding, 'ignore'), cfg)
        stdout.write('\t'.join(tok).encode('utf8') + '\n')


if __name__ == '__main__':
    main()
