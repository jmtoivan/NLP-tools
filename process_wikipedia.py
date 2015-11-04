#!/usr/bin/env python
# -*- coding: utf-8 -*-

import bz2
import gensim
import multiprocessing

# Parses a wikipedia article. Returns the content as (title, list of tokens)
def process_article((title, txt)):
    txt = gensim.corpora.wikicorpus.filter_wiki(txt) 
    return title.encode('utf8'), gensim.utils.simple_preprocess(txt)
 
# Get stuff from a bz2 Wikipedia dump as (title, tokens) -tuples.
# Ignore too short articles and redirects.
# Uses multiple processes to speed up the parsing in parallel.
 
def convert_wiki(infile, processes=multiprocessing.cpu_count()):
    pool = multiprocessing.Pool(processes)
    texts = gensim.corpora.wikicorpus._extract_pages(bz2.BZ2File(infile))
    ignore_namespaces = 'Wikipedia Category File Portal Template MediaWiki User Help Book Draft'.split()
    for group in gensim.utils.chunkize(texts, chunksize=10 * processes):
        for title, tokens in pool.imap(process_article, group):
            if len(tokens) >= 50 and not any(title.startswith(ignore + ':') for ignore in ignore_namespaces):
                yield title.replace('\t', ' '), tokens
    pool.terminate()
 
for title, tokens in convert_wiki('/path/to/enwiki-latest-pages-articles.xml.bz2'):
    print "%s\t%s" % (title, ' '.join(tokens))