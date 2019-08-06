from lingpy import *
wl = Wordlist('words.tsv')
from pyclts.transcriptionsystem import TranscriptionSystem as TS
bipa = TS('bipa')
from lingrex.util import get_c_structure


turn = {
        'ᴇ': 'ᴇ/ɛ',
        'ᴇ̃': 'ᴇ̃/ɛ̃',
        'ᴀ∼': 'ᴀ',
        '⁰⁴': '⁰⁴/¹⁴',
        '⁰²': '⁰²/¹²',
        'ᴀ̃∼': 'ᴀ̃',
        '²⁴/': '²⁴',
        '³¹/': '³¹',
        'ɔŋ': 'ɔ ŋ',
        '³²¹': '³¹²',
        'ŋ/?': 'ŋ',
        }

T = {}
ignore = []
for idx, tks, stk in wl.iter_rows('segments', 'structure'):
    
    drop = False
    newtok, newstr = [], []
    for m, s in zip(
            basictypes.lists(tks).n,
            basictypes.lists(stk).n
            ):
        newt, news = [], []
        for token, structure in zip(m, s):
            if structure in 'MN':
                newt[-1] += token
            elif structure == 'c' and token in 'iɯ':
                newt[-1] += token
            elif token == '∼':
                pass
            else:
                if structure == 'm' and token in 'uiɪy':
                    newt += [{'u': 'u/w', 'y': 'y/ɥ', 'i': 'i/j', 'ɪ': 'ɪ/j'}.get(token,
                        token)]
                else:
                    newt += [token]
                news += [structure]
        
        for i, t in enumerate(newt):
            
            s = bipa[turn.get(t, t)]
            if not s.type == 'unknownsound':
                newt[i] = s.s
            else:
                print(t, tks)
                ignore += [idx]
        newtok += [' '.join(newt)]
        newstr += [' '.join(news)]
    T[idx] = [' + '.join(newtok), ' + '.join(newstr)]

wl.add_entries('tokens', T, lambda x: x[0])
wl.add_entries('structures', T, lambda x: x[1])
print(ignore)
for idx, tks in wl.iter_rows('tokens'):
    for m in basictypes.lists(tks).n:
        cs = get_c_structure(m)
        if [x for x in cs if x not in 'imnct']:
            print(tks, '|', m, '|', cs, tokens2class(m, 'dolgo'))
wl.output('tsv', filename='words-new', ignore='all', prettify=False, 
        subset=True, rows=dict(ID="not in "+str(ignore)))
