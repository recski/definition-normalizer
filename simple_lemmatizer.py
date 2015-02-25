#processes the output of simple_tokenizer.py
#copied from various parts of pymachine.wrapper
import logging
from time import sleep
import os
import sys
import threading

from hunmisc.utils.huntool_wrapper import Hundisambig, Ocamorph, OcamorphAnalyzer, MorphAnalyzer  # nopep8

def batches(l, n):
    """ Yield successive n-sized chunks from l.
    (source: http://stackoverflow.com/questions/312443/
    how-do-you-split-a-list-into-evenly-sized-chunks-in-python
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

class SimpleThreadedLemmatizer():
    def __init__(self, hunmorph_path, no_threads=6):
        self.no_threads = no_threads
        self.tok2lemma = {}
        self.hunmorph_path = hunmorph_path

    def get_lemma(self, word):
        if word not in self.tok2lemma:
            raise Exception('need to run get_lemmas on all words first')
        return self.tok2lemma[word]

    def get_lemmas(self, words):
        batch_size = (len(words) / self.no_threads) + 1
        self.thread_states = []
        for i, batch in enumerate(batches(list(words), batch_size)):
            t = threading.Thread(
                target=self.get_lemmas_thread, args=(batch, i))
            self.thread_states.append(False)
            t.start()
        logging.info("started {0} threads, <={1} words each".format(
            len(self.thread_states), batch_size))
        while not all(self.thread_states):
            sleep(1)
        logging.info("all threads finished, printing results")

    def get_lemmas_thread(self, batch, i):
        lemmatizer = SimpleLemmatizer(self.hunmorph_path, self.tok2lemma)
        count = 0
        for word in batch:
            if count % 100 == 0:
                logging.info("thread {0}: {1} words done".format(i, count))
            count += 1
            self.tok2lemma.setdefault(word, lemmatizer.get_lemma(word))
        self.thread_states[i] = True

class SimpleLemmatizer():
    def __init__(self, hunmorph_path, tok2lemma=None):
        self.tok2lemma = {} if tok2lemma is None else tok2lemma
        self.hunmorph_path = hunmorph_path
        self.analyzer, self.morph_analyzer = self.get_analyzer()

    def get_lemmas(self, words):
        count = 0
        for word in words:
            if count % 100 == 0:
                logging.info("{0} words done".format(count))
            count += 1
            self.tok2lemma.setdefault(word, self.get_lemma(word))
        logging.info('done')

    def get_lemma(self, word, debug=False):
        if word in self.tok2lemma:
            return self.tok2lemma[word]

        lemma = list(self.analyzer.analyze(
            [[word]]))[0][0][1].split('||')[0].split('<')[0]

        self.tok2lemma[word] = lemma

        return lemma

    def get_analyzer(self):
        ocamorph = Ocamorph(
            os.path.join(self.hunmorph_path, "ocamorph"),
            os.path.join(self.hunmorph_path, "morphdb_en.bin"))
        ocamorph_analyzer = OcamorphAnalyzer(ocamorph)
        morph_analyzer = MorphAnalyzer(
            ocamorph,
            Hundisambig(
                os.path.join(self.hunmorph_path, "hundisambig"),
                os.path.join(self.hunmorph_path, "en_wsj.model")))

        return morph_analyzer, ocamorph_analyzer

def main_single_threaded():
    if len(sys.argv) > 1:
        hunmorph_path = sys.argv[1]
    else:
        hunmorph_path = "/home/recski/projects/hundisambig_compact/"
    lemmatizer = SimpleLemmatizer(hunmorph_path)
    for line in sys.stdin:
        words = line.strip().decode('utf-8').split('\t')
        lemmas = map(lemmatizer.get_lemma, words)
        print u"\t".join(lemmas).encode('utf-8')

def main():
    if len(sys.argv) > 1:
        hunmorph_path = sys.argv[1]
    else:
        hunmorph_path = "/home/recski/projects/hundisambig_compact/"
    lemmatizer = SimpleLemmatizer(hunmorph_path)
    word_lists = []
    all_words = set()
    for line in sys.stdin:
        words = line.strip().decode('utf-8').split('\t')
        word_lists.append(words)
        all_words |= set(words)

    #lemmatizer = SimpleLemmatizer(hunmorph_path)
    lemmatizer = SimpleThreadedLemmatizer(hunmorph_path)
    lemmatizer.get_lemmas(all_words)
    for words in word_lists:
        lemmas = map(lemmatizer.get_lemma, words)
        print u"\t".join(lemmas).encode('utf-8')

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s : " +
        "%(module)s (%(lineno)s) - %(levelname)s - %(message)s")
    main()
