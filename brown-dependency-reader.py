"""
Module for getting constituents from the %mor and %gram annotated Brown
corpora on CHILDES.
Barend Beekhuizen 2013
barendbeekhuizen@gmail.com
"""

import re
import sys

def read_productions(speaker,head,filenames):
    """
    Reads all productions that contain the head and are uttered by the speaker
    """
    productions = []
    files = [(open(f),f) for f in filenames]
    corpus = []
    for f in files:
        lines = re.split('\n',f[0].read())
        while lines:
            utterance = lines.pop(0)
            if re.match(('\*%s' % (speaker)), utterance):
                mor, gra = [], []
                while lines and not re.match('\%xgra', lines[0]):
                    mor.extend([re.split('\|', m) \
                                for m in re.split('[\t\s\~]', lines.pop(0))])
                while lines and (re.match('\%xgra|\t', lines[0])):
                    gra.extend([re.split('\|', m) \
                                for m in re.split('[\t\s\~]', lines.pop(0))])
                mor = [m if len(m) == 2 else ['punct', m[0]] for m in mor[1:-1]]
                gra = [[int(m[0]), int(m[1]), m[2]] for m in gra[1:-1] if len(m) == 3]
                fileid = int(re.sub('[^0-9]', '', re.split('/', f[1])[-1]))
                if next((p for p in mor if re.match(head, '|'.join(p))), None) != None:
                    corpus.append([fileid, utterance, mor, gra])
    return corpus

def get_constituents(corpus, head, depth):
    constituents = []
    for c in corpus:
        heads = [p+1 for p in xrange(len(c[2])) \
                 if re.match(head, '|'.join(c[2][p]))]
        for h in heads:
            depth_count = depth
            agenda = set([(h,h,'HEAD')])
            found = set([(h,h,'HEAD')])
            while agenda and depth_count > 0:
                depth_count -= 1
                buf = set()
                for a in agenda:
                    buf = buf | set([(d[0],d[1],d[2]) for d in c[3] \
                                     if d[0] < len(c[2])-1 \
                                     and d[1] == a[0] and d[2] != 'PUNCT'])
                found = found | buf
                agenda = buf
            sorted_depds = sorted(found, key = lambda f : f[0])
            ix_map = { sorted_depds[x][0] : x for x in xrange(len(found)) }
            constituents.append([c[0], [[ix_map[f[0]]] + c[2][f[0]-1] +
                                       [f[2],ix_map[f[1]]] for f in sorted_depds]])
    return constituents

def expand_morphology(constituents):
    new_cs = []
    for c in constituents:
        new_c = [c[0],[]]
        for d in c[1]:
            if not re.match('.*[-&]', d[2]):
                new_c[1].append(d)
            else:
                morphemes = re.split('[-&]', d[2])
                new_c[1].append([d[0], d[1], morphemes[0], d[3], d[4]])
                for m in xrange(1,len(morphemes)):
                    new_c[1].append([d[0]+0.1*m, 'infl',\
                                     morphemes[m], 'INFL', d[0]])
        new_cs.append(new_c)
    return new_cs

speaker = sys.argv[1]
head = sys.argv[2]
depth = int(sys.argv[3])
files = sys.argv[4:]
#
corpus = read_productions(speaker, head, files)
constituents = get_constituents(corpus, head, depth)
constituents = expand_morphology(constituents)
for c in constituents:
    print c
