# WSDC (Word-based Static Dictionary Compression)

WSDC is a short text compression method. It uses static word dictionaries created by training on corpora from 6 different languages (English, French, German, Italian, Spanish and Dutch) in the [DBpedia abstract corpus](https://downloads.dbpedia.org/2015-04/ext/nlp/abstracts/).

There are two levels of compression:
- At the first compression level, the language of the text is determined and the text is compressed using a 250-word dictionary of that language.
- At the second compression level, the text compressed at the first level can be further compressed using one of the sub-dictionaries created for each language.

Text compressed at both levels can be further compressed using Static Huffman Code Tables.

Approximate compression ratios (compressed size / original size):
- Only Level 1 compression: 80% - 90%
- Both Level 1 and Level 2 compression: 60% - 70%
- Level 1 compression and Static Huffman coding: 50% - 60%
- Level 1 compression, Level 2 compression and Static Huffman coding: 40% - 50% 

## USAGE
```python
wsdc.compress(text, level=2, huffman=True)
wsdc.decompress(data, level=2, huffman=True)
```