# -*- coding: utf-8 -*-

from segtok.segmenter import split_multi
from segtok.tokenizer import web_tokenizer, split_contractions

import networkx as nx
import numpy as np
import pandas as pd 
import string
import os
import math
import jellyfish
import re
import json

class DataCore(object):
    
    def __init__(self, stopword_set, windows_size, tagsToDiscard = set(['u', 'd']), exclude = set(string.punctuation)):
        self.number_of_documents = 0
        self.number_of_sentences = 0
        self.number_of_words = 0
        self.terms = {}
        self.term_vector = []
        self.candidates = {}
        self.freq_ns = {}
        
        self.G = nx.DiGraph()

        self.windowsSize = windows_size
        self.exclude = exclude
        self.tagsToDiscard = tagsToDiscard
        self.stopword_set = stopword_set

    # Build the datacore features
    # TODO: Integrity, 
    def add_document(self, text):
        text = self.pre_filter(text)
        self.number_of_documents += 1
        pos_text = 0
        document_candidates = {}
        term_in_doc = {}
        block_of_word_obj = []

        # Use a dictionary to map tokenized sentences (list of words) to original sentence
        # To avoid reconstruct the sentence from the list of tokens
        map_str_tokenized = {}
        for s in list(split_multi(text)):
            if len(s.strip()) > 0:
                map_str_tokenized[json.dumps([w for w in split_contractions(web_tokenizer(s)) if not (w.startswith("'") and len(w) > 1) and len(w) > 0])] = s

        self.number_of_sentences += len(map_str_tokenized)

        # For each tokenized sentence
        for (sentence_id, sentence) in enumerate(map_str_tokenized.keys()):

            sentence = json.loads(sentence)

            block_of_word_obj = []

            # For each word in sentence
            for (pos_sent, word) in enumerate(sentence):
                
                # Compute terms
                tag = self.get_tag(word, pos_sent)
                term_obj = self.get_term(word)
                term_in_doc[term_obj.unique_term] = term_obj
                term_obj.add_occurrence(tag, sentence_id, pos_sent, pos_text, self.number_of_documents)
                pos_text += 1
                #Create co-occurrence matrix
                if tag not in self.tagsToDiscard:
                    word_windows = list(range( max(0, len(block_of_word_obj)-self.windowsSize), len(block_of_word_obj) ))
                    for w in word_windows:
                        if block_of_word_obj[w][0] not in self.tagsToDiscard: 
                            self.add_cooccurrence(block_of_word_obj[w][2], term_obj)           

                # Add term to the block of words' buffer
                block_of_word_obj.append( (tag, word, term_obj) )

            self.number_of_words += pos_text

            # Create candidate(s)
            cand = ComposedWord(block_of_word_obj, map_str_tokenized[json.dumps(sentence)])
            cand = self.add_or_update_composed_word(cand)
            if cand.unique_kw not in document_candidates:
                document_candidates[cand.unique_kw] = cand

        return document_candidates, term_in_doc

    def compute_jaccard_similarity_score(self, x, y):
        intersection_cardinality = len(set(x).intersection(set(y)))
        union_cardinality = len(set(x).union(set(y)))
        if float(union_cardinality) == 0.:
            return 0.
        return intersection_cardinality / float(union_cardinality)

    def add_bias(self, query):
        sentences_str = [ [w for w in split_contractions(web_tokenizer(s)) if not (w.startswith("'") and len(w) > 1) and len(w) > 0] for s in list(split_multi(query)) if len(s.strip()) > 0]

        query_objs = {}
        flatten = lambda l: [item for sublist in l for item in sublist]

        for (sentence_id, sentence) in enumerate(sentences_str):
            for (pos_sent, word) in enumerate(sentence):
                if len([c for c in word if c in self.exclude]) != len(word):
                    tag = self.get_tag(word, pos_sent)
                    if tag not in self.tagsToDiscard:
                        term_obj = self.get_term(word)
                        if not term_obj.stopword and term_obj.unique_term not in query_objs:
                            query_objs[term_obj.unique_term] = (term_obj, flatten([[ out_v for (in_v, out_v) in self.G.out_edges(term_obj.id) ], [ in_v for (in_v, out_v) in self.G.in_edges(term_obj.id) ]]))
        if len(query_objs) == 0:
            return []
        to_mean = []
        for term_obj in [t for t in self.term_vector if not t.stopword]:
            term_occurs = term_obj.occurs.keys()
            jac = 0.

            term_context = flatten([[ out_v for (in_v, out_v) in self.G.out_edges(term_obj.id) ], [ in_v for (in_v, out_v) in self.G.in_edges(term_obj.id) ]])
            context_jac = 0.
            
            for query_term_obj, query_term_context in query_objs.values():
                jac += self.compute_jaccard_similarity_score(term_occurs, query_term_obj.occurs.keys())
                context_jac += self.compute_jaccard_similarity_score(term_context, query_term_context)
            if jac == 1. or  context_jac == 1.:
                term_obj.bias *= 0.05
            else:
                term_obj.bias *= (1.-(jac/len(query_objs)))*(1.-(context_jac/len(query_objs)))
        return sorted([t for t in self.term_vector if not t.stopword], key=lambda t: t.bias)

    def build_single_terms_features(self, features=None):
        validTerms = [ term for term in self.terms.values() if not term.stopword ]
        validTFs = (np.array([ x.tf for x in validTerms ]))
        avgTF = validTFs.mean()
        stdTF = validTFs.std()
        if len(self.terms.values()) == 0 or max([ x.tf for x in self.terms.values()]) == 0:
            maxTF = 1.
        else:
            maxTF = max([ x.tf for x in self.terms.values()])
        list(map(lambda x: x.updateH(maxTF=maxTF, avgTF=avgTF, stdTF=stdTF, number_of_sentences=self.number_of_sentences, features=features), self.terms.values()))

    def build_mult_terms_features(self, features=None):
        list(map(lambda x: x.updateH(features=features), [cand for cand in self.candidates.values() if cand.is_valid()]))

    def pre_filter(self, text):
        prog = re.compile("^(\\s*([A-Z]))")
        parts = text.split('\n')
        buffer = ''
        for part in parts:
            sep = ' '
            if prog.match(part):
                sep = '\n\n'
            buffer += sep + part.replace('\t',' ')
        return buffer

    def get_tag(self, word, i):
        try:
            w2 = word.replace(",","")
            float(w2)
            return "d"
        except:
            cdigit = len([c for c in word if c.isdigit()])
            calpha = len([c for c in word if c.isalpha()])
            if ( cdigit > 0 and calpha > 0 ) or (cdigit == 0 and calpha == 0) or len([c for c in word if c in self.exclude]) > 1:
                return "u"
            if len(word) == len([c for c in word if c.isupper()]):
                return "a"
            if len([c for c in word if c.isupper()]) == 1 and len(word) > 1 and word[0].isupper() and i > 0:
                return "n"
        return "p"

    def get_term(self, str_word, save_non_seen=True):
        unique_term = str_word.lower()
        simples_sto = unique_term in self.stopword_set
        if unique_term.endswith('s') and len(unique_term) > 3:
            unique_term = unique_term[:-1]

        if unique_term in self.terms:
            return self.terms[unique_term]
                
        # Include this part
        simples_unique_term = unique_term
        for pontuation in self.exclude:
            simples_unique_term = simples_unique_term.replace(pontuation, '')
        # until here
        isstopword = simples_sto or unique_term in self.stopword_set or len(simples_unique_term) < 3
        
        term_id = len(self.terms)
        term_obj = SingleWord(unique_term, term_id, self.G)
        self.term_vector.append(term_obj)
        term_obj.stopword = isstopword
        if save_non_seen:
            self.G.add_node(term_id)
            self.terms[unique_term] = term_obj
        return term_obj

    def add_cooccurrence(self, left_term, right_term):
        if right_term.id not in self.G[left_term.id]:
            self.G.add_edge(left_term.id, right_term.id, TF=0.)
        self.G[left_term.id][right_term.id]["TF"]+=1.
        
    def add_or_update_composed_word(self, cand):
        if cand.unique_kw not in self.candidates:
            self.candidates[cand.unique_kw] = cand
        else:
            self.candidates[cand.unique_kw].uptade_candidate(cand)
        self.candidates[cand.unique_kw].tf += 1.
        return self.candidates[cand.unique_kw]


class ComposedWord(object):

    def __init__(self, terms, sentence): # [ (tag, word, term_obj) ]
        if terms == None:
             self.start_or_end_stopwords = True
             self.tags = set()
             return

        self.tags = set([''.join([ w[0] for w in terms ])])
        self.unique_kw = sentence.lower()
        self.kw = sentence
        self.size = len(terms)
        self.terms = [ w[2] for w in terms if w[2] != None ]
        self.tf = 0.
        self.integrity = 1.
        self.H = 1.
        self.start_or_end_stopwords = self.terms[0].stopword or self.terms[-1].stopword

    def uptade_candidate(self, cand):
        for tag in cand.tags:
            self.tags.add( tag )

    def is_valid(self):
        # isValid = False
        # for tag in self.tags:
        #     isValid = isValid or ( "u" not in tag and "d" not in tag )
        # return isValid and not self.start_or_end_stopwords
        return True

    def get_composed_feature(self, feature_name, discart_stopword=True):
        list_of_features = [ getattr(term, feature_name) for term in self.terms if ( discart_stopword and not term.stopword ) or not discart_stopword ]
        sum_f  = sum(list_of_features)
        prod_f = np.prod(list_of_features)
        return ( sum_f, prod_f, prod_f /(sum_f + 1) )

    def updateH(self, features=None, isVirtual=False):
        sum_H  = 0.
        prod_H = 1.
        for (t, term_base) in enumerate(self.terms):
            if isVirtual and term_base.tf==0:
                continue
            if term_base.stopword:
                prob_t1 = 0.
                if t > 0:
                    if term_base.G.has_edge(self.terms[t-1].id, self.terms[ t ].id):
                        prob_t1 = term_base.G[self.terms[t-1].id][self.terms[ t ].id]["TF"] / self.terms[t-1].tf

                prob_t2 = 0.
                if t < len(self.terms)-1:
                    if term_base.G.has_edge(self.terms[ t ].id, self.terms[t+1].id):
                        prob_t2 = term_base.G[self.terms[ t ].id][self.terms[t+1].id]["TF"] / self.terms[t+1].tf

                prob = prob_t1 * prob_t2
                prod_H *= (1 + (1 - prob ) )
                sum_H += (1 - prob)
            else:
                sum_H += term_base.H
                prod_H *= term_base.H
        tf_used = 1.
        if features == None or "KPF" in features:
            tf_used = self.tf
        if isVirtual:
            tf_used = np.mean( [term_obj.tf for term_obj in self.terms] )
        self.H = prod_H / ( ( sum_H + 1 ) * tf_used )


class SingleWord(object):
    def __init__(self, unique, idx, graph):
        self.unique_term = unique
        self.id = idx
        self.tf = 0.
        self.WFreq = 0.0
        self.WCase = 0.0
        self.tf_a = 0.
        self.tf_n = 0.
        self.WRel = 1.0
        self.PL = 0.
        self.PR = 0.
        self.occurs = {}
        self.WPos = 1.0
        self.WSpread = 0.0 #DiffDistance
        self.H = 0.0
        self.stopword = False
        self.G = graph
        self.bias = 1.

        self.pagerank = 1.

    def updateH(self, maxTF, avgTF, stdTF, number_of_sentences, features=None):
        if features == None or "WRel" in features:
           # self.PL = self.WDL / maxTF
           # self.PR = self.WDR / maxTF
           # self.WRel = ( (0.5 + (self.PWL * (self.tf / maxTF) + self.PL)) + (0.5 + (self.PWR * (self.tf / maxTF) + self.PR)) )
           self.WRel = 1 + (self.PWL + self.PWR) * self.tf / maxTF

        if features == None or "WFreq" in features:
            self.WFreq = self.tf / (avgTF + stdTF)
        
        if features == None or "WSpread" in features:
            if number_of_sentences != 0:
                self.WSpread = sum([len(doc_occurs) for doc_occurs in self.occurs.values()]) / number_of_sentences
            #self.WSpread = len(self.occurs) / number_of_sentences
        
        if features == None or "WCase" in features:
            if self.tf > 0.:
                self.WCase = max(self.tf_a, self.tf_n) / (1. + math.log(self.tf))
        
        if features == None or "WPos" in features:
            flatten = lambda l: [item for sublist in l for item in sublist]
            self.WPos = math.log( math.log( 3. + np.median(flatten([list(doc_occur.keys()) for doc_occur in self.occurs.values()])) ) )
            #self.WPos = math.log( math.log( 3. + np.median(list(self.occurs.keys())) ) )

        self.H = self.bias * (self.WPos * self.WRel) / (self.WCase + (self.WFreq / self.WRel) + (self.WSpread / self.WRel))
        
    @property
    def WDR(self):
        return len( self.G.out_edges(self.id) )

    @property
    def WIR(self):
        return sum( [ d['TF'] for (u,v,d) in self.G.out_edges(self.id, data=True) ] )

    @property
    def PWR(self):
        wir = self.WIR
        if wir == 0:
            return 0
        return self.WDR / wir 
    
    @property
    def WDL(self):
        return len( self.G.in_edges(self.id) )

    @property
    def WIL(self):
        return sum( [ d['TF'] for (u,v,d) in self.G.in_edges(self.id, data=True) ] )
        
    @property
    def PWL(self):
        wil = self.WIL
        if wil == 0:
            return 0
        return self.WDL / wil 

    def add_occurrence(self, tag, sent_id, pos_sent, pos_text, docid=0):
        if docid not in self.occurs:
            self.occurs[docid] = {}
        if sent_id not in self.occurs[docid]:
            self.occurs[docid][sent_id] = []
        self.occurs[docid][sent_id].append( (pos_sent, pos_text) )
        self.tf += 1.
        if tag == "a":
            self.tf_a += 1.
        if tag == "n":
            self.tf_n += 1.
