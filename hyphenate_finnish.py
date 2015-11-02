#!/usr/bin/env python
# -*- coding: utf-8 -*-

#--------------------------------------------------#
# A python script to hyphenate Finnish		   #
#                                                  #
#--------------------------------------------------#

import re, nltk

def main():
    text = u'Kokoelmien köyhyyttäsi sydämien avarammiks pieniks löydettais tähdistö.'
    
    l = divide_word(clean(text))
    for w in l:
        print w
    #for word in clean(text).split(' '):
	#print word, how_many_syllables(word)
   
    
def divide_word(word):
    syllables = []
    c = ur'[bcdfghjklmnpqrstvwxz]'
    v = ur'[aeiouyäö]'
    diphthong = ur'''(?x)
                aa|ai|au
                |ee|ei|eu|ey
                |ie|ii|iu
                |oi|oo|ou
                |ui|uo|uu
                |yi|yy|yö
                |äi|ää|äy
                |öi|öy|öö
                '''

    #Consonant rule: If there are one or more consonants following a vowel
    #in a syllable and still a vowel after the consonants the last two
    #consonants are separated by a hyphen.
    
    cRule = ur'(%s+%s*)(%s(?!%s?$))'
    cRuleSyl = re.compile(cRule%(v,c,c,c))
    
    #Diphthong rules: A diphthong and a vowel are always separated
    #by a hyphen. 

    vowelRule = ur'(%s)(%s)'
    diphthongRuleSyl1 = re.compile(vowelRule%(diphthong,v))
    diphthongRuleSyl2 = re.compile(vowelRule%(v,diphthong))    
   
    #Vowel rules: For every vowel there are several vowels that do not form a
    #diphthong. In this case they are separated by a hyphen.

    aRule = re.compile(ur'(a)([eoyäö])')
    eRule = re.compile(ur'(e)([aoäö])')
    iRule = re.compile(ur'(i)([aoyäö])')
    oRule = re.compile(ur'(o)([aeyäö])')
    uRule = re.compile(ur'(u)([aeyäö])')
    yRule = re.compile(ur'(y)([aeouä])')
    aeRule = re.compile(ur'(ä)([aeouö])')
    oeRule = re.compile(ur'(ö)([aeouä])')

    #No hyphen in front of two consonants in the end of the word.

    w = word.split(" ")
    for i in range(len(w)):
        m = cRuleSyl.sub(r'\1-\2', w[i])
        m = diphthongRuleSyl1.sub(r'\1-\2', m)
        m = diphthongRuleSyl2.sub(r'\1-\2', m)
        m = aRule.sub(r'\1-\2', m)
        m = eRule.sub(r'\1-\2', m)
        m = iRule.sub(r'\1-\2', m)
        m = oRule.sub(r'\1-\2', m)
        m = uRule.sub(r'\1-\2', m)
        m = yRule.sub(r'\1-\2', m)
        m = aeRule.sub(r'\1-\2', m)
        m = oeRule.sub(r'\1-\2', m)
        syllables.append(m)
    
    return syllables

def clean(text):
    text = text.lower()
    cleanRule = re.compile(ur'[\_\´\`\^\+\/\(\)\>\<\*\[\]\{\}\=\&\@\$\\,.:;\'\"?!\-%#\d]')
    clean = cleanRule.sub(r'', text)
    return clean

def how_many_syllables(word):
    l = divide_word(word)
    syl = l[0].split("-")
    return len(syl)

def syllables_in_line(line):
    if line == '':
        return 0
    l = line.split(' ')
    num_syl = 0
    for w in l:
        num_syl = num_syl + how_many_syllables(w)
    return num_syl


if __name__ == "__main__":
    main()
