from scipy.sparse import csgraph, csr_matrix, dok_matrix
from sys import argv

def read_definitions_to_array(fn):
    f = open(fn)
    labels = dict()
    labels_n = 0
    D = dok_matrix((50630, 50630))
    for l in f:
        fd = l.decode('utf8').strip().split('\t')
        dm = fd[0]
        if not dm in labels:
            labels[dm] = labels_n
            labels_n += 1
        for ds in fd[1:]:
            if not ds in labels:
                labels[ds] = labels_n
                labels_n += 1
            D[labels[dm],labels[ds]] = 1
    f.close()
    return csr_matrix(D), labels

def write_components_to_file(n, comps, labels, fn, fn2=None):
    f = open(fn, 'w')
    if fn2:
        f2 = open(fn2, 'w')
    classes = [[] for i in range(n)]
    for i, cl in enumerate(comps):
        classes[cl].append(labels[i])
    for cl in classes:
        f.write('\t'.join(cl).encode('utf8') + '\n')
        if fn2:
            if len(cl) > 1:
                f2.write('\t'.join(cl).encode('utf8') + '\n')
    if fn2:
        f2.close()
    f.close()

def main():
    arr, labels = read_definitions_to_array(argv[1])
    print "Definitions read"
    comp_n, comp_labels = csgraph.connected_components(
        arr, directed=True, connection='strong')
    print "Numer of components: " + str(comp_n)
    write_components_to_file(comp_n, comp_labels, 
         dict(((v, k) for k, v in labels.iteritems())), argv[2], argv[3])


if __name__ == '__main__':
    main()
