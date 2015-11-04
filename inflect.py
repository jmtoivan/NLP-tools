#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This module is does morphology processing in Finnish.
# It provides the following functionalities:
# (1): For a list of words gives their POS tags
# (2): For a given word finds it morphological analysis and produces similar
# morphological form out of a given lemma
# Arguments: ['word_1', 'lemma_2'] -> 'lemma_2_in_form_1'

# This module uses HFST and its python bindings.
# More information on HFST and the installation guidelines can
# be found at: https://kitwiki.csc.fi/twiki/bin/view/KitWiki/HfstHome

import os, sys, 
import re 
import libhfst
from itertools import ifilterfalse as ffilter

datadir = "./morphology_sets/"
analysis_set = os.path.abspath(datadir + "/morphology.omor.hfstol")
generation_set = os.path.abspath(datadir + "/generation.omor.hfstol")


istr1 = libhfst.HfstInputStream(analysis_set)
istr2 = libhfst.HfstInputStream(generation_set)
analyser = libhfst.HfstTransducer(istr1)
synthetiser = libhfst.HfstTransducer(istr2)

def main():

    print get_inflection(u'lampaallenikaan', u'kääpiösnautseri')


# (1): takes a list of words, gives pos tags
def get_POS_list(word_list):
    POS_list = []
    line = ''
    for word in word_list:
        analysis = analyser.lookup_fd(str(word.encode('utf-8')))
        results = process_result_vector(libhfst.vectorize(analysis))
        POS = get_POS_tag(results[0][0])
        POS_list.append(POS)
    return POS_list

# (2): takes a word, gives its morphological analysis and for a second word (lemma) inflects 
#it to the corresponding form
def get_inflection(inflected_word, word_to_inflect):
    analysis = get_analysis(inflected_word)
    if analysis == None:
    	return None
    #print('ANALYSIS ', analysis)
    new_analysis = clean_analysis(inflected_word, analysis)
    #print('NEW ANALYSIS ', new_analysis)
    lemma = get_lemma(new_analysis)
    #print(new_analysis)
    
    #Change the KTN tag for nouns, verbs, numerals and adjectives.
    #Add, change or remove the KAV tag.
    pos = get_POS_tag(analysis)
    if (pos == 'POS=NOUN') or (pos == 'POS=VERB') or\
       (pos == 'POS=NUMERAL') or (pos == 'POS=ADJECTIVE'):
        analysis2 = get_analysis(word_to_inflect)
        if analysis2 == None:
        	return None
        #Only the analysis of the head word is needed
        analysis_head = get_head(analysis2)
        lemma2 = get_lemma(analysis_head)
        new_analysis = change_KTN_tag(new_analysis, analysis_head)
        new_analysis = change_KAV_tag(new_analysis, analysis_head)
        #If word_to_inflect is a compound, add the analysis of the modifiers
        new_analysis = add_modifier(new_analysis, analysis2)
    else:
        lemma2 = word_to_inflect
        
    new_analysis = new_analysis.replace(lemma, lemma2)
    #print('NEW ANALYSIS ', new_analysis)
    new_word = generate_word(new_analysis)
    if new_word != None:
        #The generation was succeeded
        return new_word
    else:
        #The allo tag may be wrong. Let's try to change it.
        new_word = change_allo_tag(new_analysis)
        #print new_word
        if new_word != None:
            return new_word
        else:
            return None

#Makes the analysis readable for the automaton that generates word forms
def clean_analysis(word, analysis):
    analysis = get_head(analysis)
    #Remove white spaces
    analysis = analysis.strip()
    #Remove the zeros and the dot in the end
    analysis = analysis.rstrip('0.')
    #Remove the rest of the white spaces
    return analysis.strip()

#From the analysis of a compound, returns the analysis of the head word
def get_head(analysis):
    if analysis == None:
    	return None
    compound_index = analysis.rfind('=COMPOUND]')
    if compound_index != -1:
        lemma_index = analysis.find('[LEMMA=')
        #Remove everything from '[LEMMA=' to '=COMPOUND]'
        analysis = analysis[0:lemma_index]+\
                   analysis[compound_index+10:len(analysis)]
    return analysis

#Adds the analysis of the modifiers in analysis2 to analysis
def add_modifier(analysis, analysis2):
    compound_index = analysis2.rfind('=COMPOUND]')
    if compound_index != -1:
        lemma_index = analysis2.find('[LEMMA=')
        #Save everything from '[LEMMA=' to '=COMPOUND]'
        modifier = analysis2[lemma_index:compound_index+10]
        #modifier = unicode(modifier, 'utf-8')
        start_tag = analysis.find('=LEXITEM]')
        analysis = analysis[0:start_tag+9] + modifier +\
                       analysis[start_tag+9:len(analysis)]
    return analysis

#Gives the analysis the correct KTN tag for word form generation.
#Takes the analysis of a word and gives it the KTN tag of another word. 
def change_KTN_tag(analysis, analysis2):
    ktn = re.search(ur'(?<=KTN\=)[0-9]{1,2}', analysis2)
    if not ktn:
        #If no KTN tag is found, keep the analysis unchanged
        return analysis
    else:
        new_analysis = re.sub(ur'(?<=KTN\=)[0-9]{1,2}', ktn.group(0), analysis)
        return new_analysis

#If analysis and analysis2 have KAV tags, replace the first with the second.
#If analysis has a KAV tag, remove it.
#If analysis2 has a KAV tag, insert it to analysis.
def change_KAV_tag(analysis, analysis2):
    kav1 = re.search(ur'\[KAV\=[A-Z]\]', analysis)
    kav2 = re.search(ur'\[KAV\=[A-Z]\]', analysis2)
    if not kav1 and not kav2:
        #No KAV tags, don't do anything
        return analysis
    elif kav1 and not kav2:
        #Remove the KAV tag from analysis
        return analysis.replace(kav1.group(), '')
    elif kav1 and kav2:
        #Replace the KAV tag of analysis with the KAV tag of analysis2
        return analysis.replace(kav1.group(), kav2.group())
    elif not kav1 and kav2:
        #Insert the KAV tag of analysis2 to analysis
        index = analysis.find('[NUM=')
        return analysis[0:index] + kav2.group() + analysis[index:len(analysis)]
    else:
        return analysis

#Finds the correct ALLO tag and generates the word.
#The lemma and the ktn tag have to be correct!
#PL GEN: IEN, JEN, TEN, ITTEN, IDEN
#SG PAR: A, TA
#PL PAR: IA, JA, ITA
#SG ILL: VN, HVN, SEEN (V = vowel)
#PL ILL: IIN, IEN, ISIIN
def change_allo_tag(analysis):
    allo = get_allo_tag(analysis)
    case = get_case_tag(analysis)
    num = get_num_tag(analysis)    
    if num == 'NUM=PL' and case == 'CASE=GEN':
        return try_allo_tags(analysis, ['IEN', 'JEN', 'TEN', 'IDEN', 'ITTEN'], allo)
    elif num == 'NUM=SG' and case == 'CASE=PAR':
        return try_allo_tags(analysis, ['A', 'TA'], allo)
    elif num == 'NUM=PL' and case == 'CASE=PAR':
        return try_allo_tags(analysis, ['IA', 'JA', 'ITA'], allo)
    elif num == 'NUM=SG' and case == 'CASE=ILL':
        return try_allo_tags(analysis, ['VN', 'HVN', 'SEEN'], allo)
    elif num == 'NUM=PL' and case == 'CASE=ILL':
        return try_allo_tags(analysis, ['IIN', 'IEN', 'ISIIN'], allo)
    else:
        return analysis

#Try to generate the word with different allo tags.
def try_allo_tags(analysis, allo_list, allo):
    for a in allo_list:
        new_analysis = analysis.replace(allo, 'ALLO='+a)
        #print(new_analysis)
        word = generate_word(new_analysis)
        if word != None:
            #The correct allo tag was found, stop the process.
            #print(word)
            return word
    #The correct allo tag was not found, return the original analysis.
    return analysis

def get_analysis(word):
    analysis = analyser.lookup_fd(str(word.encode('utf-8')))
    results = process_result_vector(libhfst.vectorize(analysis))
    if results == []:
    	return None
    analysis = unicode(results[0][0], encoding='utf-8')
    return analysis

def generate_word(analysis):
    word = synthetiser.lookup_fd(str(analysis.encode('utf-8')))
    results = process_result_vector(libhfst.vectorize(word))
    if len(results) != 0:
        word = unicode(results[0][0], encoding='utf-8')
        return word
    else:
        return None

def lemma(word):
    analysis = get_analysis(word)
    if analysis != None:
        lemma = get_lemma(analysis)
        return lemma
    else:
        return -1

def pos(word):
    analysis = get_analysis(word)
    if analysis != None:
        pos = get_POS_tag(analysis)
        return pos
    else:
        return -1

def get_lemma(analysis_string):
    m = re.search(u'LEMMA=[a-zäöåA-ZÄÖÅ\'.,:;!?]*', analysis_string)
    if m == None:
        return ''
    else:
        m = re.sub(ur'[\']', '', m.group(0))
        m = m.replace('LEMMA=', '')
        return m

def get_POS_tag(analysis_string):
    m = re.findall(u'POS=[ABCDEFGHIJKLMNOPQRSTUVWXYZÅÄÖ]*', analysis_string)
    if len(m) > 1 and 'POS=ADJECTIVE' in m:
        return 'POS=ADJECTIVE'
    else:
        m = re.search(u'POS=[ABCDEFGHIJKLMNOPQRSTUVWXYZÅÄÖ]*', analysis_string)
    if m == None:
        return ''
    else:
        return m.group(0)

def get_num_tag(analysis_string):
    m = re.search(u'NUM=[ABCDEFGHIJKLMNOPQRSTUVWXYZÅÄÖ]*', analysis_string)
    if m == None:
        return ''
    else:
        return m.group(0)

def get_case_tag(analysis_string):
    m = re.findall(u'CASE=[ABCDEFGHIJKLMNOPQRSTUVWXYZÅÄÖ]*', analysis_string)
    if 'BOUNDARY=COMPOUND' in analysis_string and len(m) > 1:
        return m[-1]
    elif len(m) > 1:
        return m[0]
    else:
        m = re.search(u'CASE=[ABCDEFGHIJKLMNOPQRSTUVWXYZÅÄÖ]*', analysis_string)
    if m == None:
        return ''
    else:
        return m.group(0)

def get_allo_tag(analysis_string):
    m = re.search(u'ALLO=[ABCDEFGHIJKLMNOPQRSTUVWXYZÅÄÖ]*', analysis_string)
    if m == None:
        return ''
    else:
        return m.group(0)

def process_result_vector(vector):
    results = []
    for entry in vector:
        if len(entry) < 2:
            continue
        weight = entry[0]
        string = ''.join(ffilter(libhfst.FdOperation.is_diacritic, entry[1]))
        results.append((string, weight))
    return results

if __name__ == '__main__':
    main()
