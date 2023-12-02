import wsdc_dict as dicts
import wsdc_inverted_dict as inv_dicts
from huff import huffman_encode, huffman_decode

langs = ["de", "en", "es", "fr", "it", "nl"]
words = []
dictionary = []

def encode():
    level2_dict = {}
    s = 0
    for i in dictionary:
        level2_dict[i] = s
        s += 1
    nc, sn, bn = [], [], []
    b, p = 0, 7
    for k in words:
        kodlandi = False
        i = level2_dict.get(k)
        if i is not None:
            sn.append(i)
            kodlandi = True
        elif k[-1] in ['.', ',', ')']:
            i = level2_dict.get(k[:-1])
            if i is not None:
                if k[-1] == '.': 
                    sn.append(250)
                elif k[-1] == ',': 
                    sn.append(251)
                elif k[-1] == ')':
                    sn.append(252)
                sn.append(i)
                kodlandi = True
        elif k[0] == '(':
            i = level2_dict.get(k[1:])
            if i is not None:  
                sn.append(253)
                sn.append(i)
                kodlandi = True
        elif k.isupper():
            i = level2_dict.get(k.lower())
            if i is not None: 
                sn.append(255)
                sn.append(i)
                kodlandi = True
        elif k[0].isupper():
            i = level2_dict.get(k[0].lower() + k[1:])
            if i is not None: 
                sn.append(254)
                sn.append(i)
                kodlandi = True

        if kodlandi:
            b += 2 ** p
        else:
            nc.append(k + ' ')

        if p == 0:
            bn.append(b)
            b, p = 0, 7
        else:
            p -= 1

    bn.append(b)  # Even if the 8-bit is not full, we must write the part containing the last bits.
    nc = ''.join(nc)[:-1]  # are merged and the last 1 space is deleted.
    return nc, bytes(sn), bytes(bn)

def compress(text, level=2, huffman=True):
    global words, dictionary
    words = text.split()
    dictionaries = []
    for i in langs:
        dictionaries += [dicts.level1_dict[i]]

    # LeveL 1: language detection
    counter = dict.fromkeys(langs, 0)
    for i in words:
        for k in inv_dicts.inv_dict1.get(str(i), []):
            # counter[k] += 1         # counter increases by '1'
            counter[k] += len(i) - 1  # counter increases by 'word size-1'
    lang = max(counter, key=counter.get)
    dictionary = dicts.level1_dict[lang]

    # Level 1 compression
    nc, s1, b1 = encode()

    if level == 1:
        # Added to avoid errors with large files (accepted that there can be a maximum of 64 languages)
        if len(s1) > 16777215:
            header = bytes().join([bytes([langs.index(lang) + 192]), len(b1).to_bytes(4), len(s1).to_bytes(4)])
        elif len(s1) > 65535:
            header = bytes().join([bytes([langs.index(lang) + 128]), len(b1).to_bytes(3), len(s1).to_bytes(3)])
        elif len(s1) > 255:
            header = bytes().join([bytes([langs.index(lang) + 64]), len(b1).to_bytes(2), len(s1).to_bytes(2)])
        else:
            header = bytes([langs.index(lang), len(b1), len(s1)])
        if huffman:
            return bytes().join([header, b1, s1, huffman_encode(nc, lang)])
        else:
            return bytes().join([header, b1, s1, bytes(nc, 'utf8')])

    # 2nd level dictionaries for the language identified in the 1st level are selected.
    dictionaries2 = dicts.level2_dict[lang]
    inv_dictionaries2 = inv_dicts.inv_dict2[lang]
    words = nc.split()

    # LeveL 2: subject detection
    counter = [0 for i in range(len(dictionaries2))]
    for i in words:
        for k in inv_dictionaries2.get(i, []):
            # counter[k] += 1         # counter increases by '1'
            counter[k] += len(i) - 1  # counter increases by 'word size-1'
    dictionary_no = counter.index(max(counter))
    dictionary = dictionaries2[dictionary_no]

    # Level 2 compression
    nc, s2, b2 = encode()

    # Added to avoid errors with large files (accepted that there can be a maximum of 64 languages)
    if len(s1) > 16777215 or len(s2) > 16777215:
        header = bytes().join([bytes([langs.index(lang) + 192, dictionary_no]), len(b1).to_bytes(4), len(s1).to_bytes(4),
                               len(b2).to_bytes(4), len(s2).to_bytes(4)])
    elif len(s1) > 65535 or len(s2) > 65535:
        header = bytes().join([bytes([langs.index(lang) + 128, dictionary_no]), len(b1).to_bytes(3), len(s1).to_bytes(3),
                               len(b2).to_bytes(3), len(s2).to_bytes(3)])
    elif len(s1) > 255 or len(s2) > 255:
        header = bytes().join([bytes([langs.index(lang) + 64, dictionary_no]), len(b1).to_bytes(2), len(s1).to_bytes(2),
                           len(b2).to_bytes(2), len(s2).to_bytes(2)])
    else:
        header = bytes([langs.index(lang), dictionary_no, len(b1), len(s1), len(b2), len(s2)])
    if huffman:
        return bytes().join([header, b1, s1, b2, s2, huffman_encode(nc, lang)])
    else:
        return bytes().join([header, b1, s1, b2, s2, bytes(nc, 'utf8')])

def decode(nc, bn, sn):
    words = nc.split()
    nc = []
    try:
        si, ki = 0, 0
        for b in bn:
            p = 8
            while p:
                p -= 1
                if b // 2 ** p % 2:
                    item = sn[si]
                    if item < 250:
                        nc.append(dictionary[item])
                        nc.append(' ')
                    else:
                        si += 1
                        nc.append(dictionary[sn[si]])
                        if item == 250:
                            nc.append('. ')
                        elif item == 251:
                            nc.append(', ')
                        elif item == 252:
                            nc.append(') ')
                        elif item == 253:
                            nc.insert(-1, '(')
                            nc.append(' ')
                        elif item == 254:
                            nc[-1] = nc[-1].capitalize()
                            nc.append(' ')
                        elif item == 255:
                            nc[-1] = nc[-1].upper()
                            nc.append(' ')
                    si += 1
                else:
                    nc.append(words[ki])
                    nc.append(' ')
                    ki += 1
    except:
        pass
    return ''.join(nc).rstrip()

def decompress(data, level=2, huffman=True):
    global dictionary
    lang = langs[int(data[0]) % 64]
    if level == 1:
        dictionary = dicts.level1_dict[lang]
        if data[0] > 192:
            header_size = 9
            lb1 = int.from_bytes(data[1:5])
            ls1 = int.from_bytes(data[5:header_size])
        elif data[0] > 128:
            header_size = 7
            lb1 = int.from_bytes(data[1:4])
            ls1 = int.from_bytes(data[4:header_size])
        elif data[0] > 64:
            header_size = 5
            lb1 = int.from_bytes(data[1:3])
            ls1 = int.from_bytes(data[3:header_size])
        else:
            header_size = 3
            lb1 = int(data[1])
            ls1 = int(data[2])
        b1 = data[header_size:header_size + lb1]
        s1 = data[header_size + lb1:header_size + lb1 + ls1]
        if huffman:
            data = huffman_decode(data[header_size + lb1 + ls1:], lang)
        else:
            data = data[header_size + lb1 + ls1:].decode(encode='utf8', errors='ignore')
        data = decode(data, b1, s1)
    else:
        dictionary_no = int(data[1])
        dictionary = dicts.level2_dict[lang][dictionary_no]
        if data[0] > 192:
            header_size = 18
            lb1 = int.from_bytes(data[2:6])
            ls1 = int.from_bytes(data[6:10])
            lb2 = int.from_bytes(data[10:14])
            ls2 = int.from_bytes(data[14:header_size])
        elif data[0] > 128:
            header_size = 14
            lb1 = int.from_bytes(data[2:5])
            ls1 = int.from_bytes(data[5:8])
            lb2 = int.from_bytes(data[8:11])
            ls2 = int.from_bytes(data[11:header_size])
        elif data[0] > 64:
            header_size = 10
            lb1 = int.from_bytes(data[2:4])
            ls1 = int.from_bytes(data[4:6])
            lb2 = int.from_bytes(data[6:8])
            ls2 = int.from_bytes(data[8:header_size])
        else:
            header_size = 6
            lb1 = int(data[2])
            ls1 = int(data[3])
            lb2 = int(data[4])
            ls2 = int(data[5])
        b1 = data[header_size:header_size+lb1]
        s1 = data[header_size+lb1:header_size+lb1+ls1]
        b2 = data[header_size+lb1+ls1:header_size+lb1+ls1+lb2]
        s2 = data[header_size+lb1+ls1+lb2:header_size+lb1+ls1+lb2+ls2]
        if huffman:
            data = huffman_decode(data[header_size+lb1+ls1+lb2+ls2:], lang)
        else:
            data = data[header_size + lb1 + ls1 + lb2 + ls2:].decode(encode='utf8', errors='ignore')
        data = decode(data, b2, s2)
        dictionary = dicts.level1_dict[lang]
        data = decode(data, b1, s1)
    return data
