# -*- coding: utf-8 -*-

from .datacore import DataCore

from itertools import repeat
from collections import Counter, namedtuple
from os import path
from scipy import signal
from glob import glob
from .Levenshtein import Levenshtein
import time
import numpy as np
from stop_words import get_stop_words
import multiprocessing
from joblib import Parallel, delayed

ProcessedHeadline = namedtuple('ProcessedHeadline', ['info', 'candidates', 'terms'])
Keyphrase = namedtuple('Keyphrase', ['kw', 'cand_obj', 'headlines'])
Term = namedtuple('Term', ['term', 'tf', 'h'])

class TemporalSummarizationEngine(object):
	
	def __init__(self, windows_size=2, top=20, similarity_threshold=0.8):
		self.windows_size = windows_size
		self.stopwords = {}
	
		self.top = top
		self.similarity_threshold = similarity_threshold

	def get_index_of(self, t, intervals):

		for (i,(min_i, max_i)) in enumerate(intervals):
			if min_i <= t < max_i:
				return i

		return None

	def get_chunk(self, sorted_resultset, qtd_intervals_param = 60, order = 2, percent=0.05):

		if len(sorted_resultset) < 2:
			return []

		times = [ x.info.datetime for x in sorted_resultset ]
		
		interval_in_days = (times[-1]-times[0]).days
		number_of_intervals = min(qtd_intervals_param, interval_in_days)
		size_time_interval = (times[-1]-times[0])/number_of_intervals

		intervals = [ (i*size_time_interval+times[0], (i+1)*size_time_interval+times[0]) for i in range(number_of_intervals) ]
		interval_index = [ self.get_index_of(t, intervals) for t in times ]

		cnt = Counter(interval_index)

		array_counted = []
		for virtual_index in range(order):
			array_counted.append( cnt[0]/((order-virtual_index)+1) )

		array_counted.extend([ cnt[c] for c in range(number_of_intervals) ])

		for virtual_index in range(order):
			array_counted.append( cnt[number_of_intervals-1]/(virtual_index+2) )

		indexes, = signal.argrelextrema(np.array(array_counted),comparator=np.greater,order=order)
		
		centers = []
		for i, c in enumerate(indexes[1:]):
			idx_break = indexes[i] + np.argmin(array_counted[indexes[i]:c])
			centers.append(intervals[idx_break-order][1])
		
		idx_chunk = 0
		chunks = []
		atual_chunk = []
		
		for idx_proc, time_proc in enumerate(times):
			
			if idx_chunk == len(centers): 
				break
		
			if time_proc > centers[idx_chunk]:
				idx_chunk += 1
				chunks.append(atual_chunk)
				atual_chunk = []
			atual_chunk.append(sorted_resultset[idx_proc])

		for idx_proc, time_proc in list(enumerate(times))[idx_proc:]:
			atual_chunk.append(sorted_resultset[idx_proc])
		
		chunks.append(atual_chunk)
		
		min_size_chunk = max(50, percent * max([ len(chunk) for chunk in chunks ]), percent * len(sorted_resultset) )
		final_chunks = []
		atual_chunk = []
		
		for chunk in chunks:
			atual_chunk.extend(chunk)
			if len(atual_chunk) > min_size_chunk:
				final_chunks.append(atual_chunk)
				atual_chunk = []
		
		if len(atual_chunk) > 0:
			if len(atual_chunk) > min_size_chunk:
				final_chunks.append(atual_chunk)
			elif len(final_chunks) > 0:
				final_chunks[-1].extend(atual_chunk)

		return final_chunks

	def proc_chunk(self, chunk):

		from_chunk_datetime = chunk[0].info.datetime
		to_chunk_datetime = chunk[-1].info.datetime
		kws = set()
		seen = set()
		to_analyse = []
		
		for doc_proc in chunk:
			# Sort by relevance
			cands = sorted(doc_proc.candidates, key=lambda x: x.cand_obj.H)
			for kw in cands:
				if kw.kw not in kws:
					kws.add(kw.kw)
					# Include only one entry per news
					if doc_proc.info not in seen:
						seen.add(doc_proc.info)
						to_analyse.append(kw)

		result_chunk, _ = self.extract_keyphrases(to_analyse)

		result_interval = { 
			'from':from_chunk_datetime, 
			'to':to_chunk_datetime, 
			'n_docs': len(chunk), 
			'keyphrases': result_chunk 
		}

		return result_interval

	def build_intervals(self, resultset, lan, query, use_headline=True, top_terms=20):
		
		if(len(resultset) == 0):
			return

		processing_time = time.time()
		
		sorted_resultset = sorted(resultset, key=lambda x: x.datetime)
		sorted_resultset = self.evaluate_unique_headlines(sorted_resultset, use_headline=use_headline)
		
		stopwords = get_stop_words(lan)
		
		dc = DataCore(windows_size=self.windows_size, stopword_set=stopwords)
		
		processed_headline = []
		result_domains = []
		
		domain_id = {}
		all_key_candidates= {}
		
		news_for_timeline = []

		for result in sorted_resultset:
			# Set use_headline to False to use titles in tls-covid (ONLY in tls-covid, or datasets where both headline and title exist in ResultHeadline)
			if use_headline:
				document_candidates, term_in_doc = dc.add_document(result.headline)
			else:
				document_candidates, term_in_doc = dc.add_document(result.title)
		
			proc_head = ProcessedHeadline(info=result, candidates=[], terms=term_in_doc)

			if proc_head.info.domain not in domain_id:
				domain_id[proc_head.info.domain] = len(result_domains)
				result_domains.append(proc_head.info.domain)
			
			news_for_timeline.append( (str(proc_head.info.datetime), domain_id[proc_head.info.domain]) )

			for cand, cand_obj in document_candidates.items():

				if cand not in all_key_candidates:
					all_key_candidates[cand] = Keyphrase( kw=cand_obj.unique_kw, cand_obj=cand_obj, headlines=[])

				all_key_candidates[cand].headlines.append(proc_head)

				if cand_obj.is_valid():
					proc_head.candidates.append(all_key_candidates[cand])

			processed_headline.append(proc_head)
		
		terms_correlations = [ (term_obj.unique_term, 1.-term_obj.bias) for term_obj in dc.add_bias(query)]
		dc.build_single_terms_features()
		dc.build_mult_terms_features()
		
		# get top_terms most relevant terms (smaller H), excluding stopwords
		# term is namedtuple Term
		most_relevant_terms = [Term(term=t, tf=sw.tf, h=sw.H) for t, sw in dc.terms.items() if not sw.stopword]
		most_relevant_terms = sorted(most_relevant_terms, key=lambda term: term.h)
		most_relevant_terms = most_relevant_terms[:top_terms]

		chunks = self.get_chunk(processed_headline)

		# Parallelize chunks processing
		num_cores = multiprocessing.cpu_count()

		if num_cores > 1:
			num_cores = int(num_cores/2)

		general_array_results = []
		general_array_results.extend(Parallel(n_jobs=num_cores)(delayed(self.proc_chunk)(chunk) for chunk in chunks))
		
		total_time_spent = time.time() - processing_time
		
		dict_result = {
			'query': query,
			'status': 'OK',
			'stats': {
				'n_unique_docs': len(processed_headline), 
				'n_docs':len(resultset), 
				'n_domains': len(result_domains),
				'time': total_time_spent
			},

			'domains': result_domains,
			'query_term_corr': terms_correlations[:self.top*2],
			'results': general_array_results,
			'news_for_timeline': news_for_timeline,
			'most_relevant_terms': most_relevant_terms
		}
	
		return dict_result

	def evaluate_unique_headlines(self, resultset, use_headline=True):
		final_resultset = []
		unique_headlines = set()

		for hl in resultset:
			if use_headline:
				if hl.headline not in unique_headlines:
					unique_headlines.add(hl.headline)
					final_resultset.append(hl)
			else:
				if hl.title not in unique_headlines:
					unique_headlines.add(hl.title)
					final_resultset.append(hl)

		return final_resultset

	def extract_keyphrases(self, to_analyse, min_size=4):
		general_results = []
		keywords = []
		to_analyse = [ kw for kw in to_analyse if kw.cand_obj.size >= min_size ]
		to_analyse = sorted(to_analyse, key=lambda x: x.cand_obj.H)

		for kw in to_analyse:
			if self.evaluate_levenshtein_distance(keywords, kw):
				general_results.append( kw )
				keywords.append(kw)

			if len(general_results) == self.top:
				break

		general_results = sorted(general_results, key=lambda x: min([ t.info.datetime for t in x.headlines ]))
		return general_results, keywords

	

	def evaluate_levenshtein_distance(self, all_kw, kw):
		'''evaluate if keyphrase is different enought from others candidates'''

		for kw2 in all_kw:
			dd = Levenshtein.ratio(kw.cand_obj.unique_kw, kw2.cand_obj.unique_kw)
			
			if dd > self.similarity_threshold or kw.cand_obj.unique_kw in kw2.cand_obj.unique_kw or kw2.cand_obj.unique_kw in kw.cand_obj.unique_kw:
				return False

		return True			
	
	def serialize(self, result, tls_covid=False):
		serialized = {
			'query': result['query'],
			'status': result['status'],
			'domains':result['domains'],
			'stats': result['stats'],
			'query_term_corr': result['query_term_corr'],
			'news_for_timeline': result['news_for_timeline'],
			'most_relevant_terms': result['most_relevant_terms']
		}

		serialized['results'] = []

		for chunk in result['results']:
			result_chunk = []
			for result_key in chunk['keyphrases']:

				data = { 
					'kw': result_key.cand_obj.kw,
					'date': str(min([ t.info.datetime for t in result_key.headlines if chunk['from'] <= t.info.datetime <= chunk['to']])), 
					'docs': [(t.info.headline, t.info.url) for t in result_key.headlines] 
				}

				if tls_covid:
					data['title'] = str(result_key.headlines[0].info.title)
					data['is_km'] = str(result_key.headlines[0].info.is_km)

				result_chunk.append(data)

			result_chunk = sorted(result_chunk, key=lambda kw_dict: kw_dict['date'] )
			result_interval = { 'from':str(chunk['from']), 
								'to':str(chunk['to']), 
								'n_docs': len(chunk), 
								'keyphrases': result_chunk 
							  }

			serialized['results'].append(result_interval)

		return serialized

	def pprint(self, intervals, verbose=False):
		
		n_docs = 0
		n_domains = 0

		if (intervals):
			print()
			print("Timeline")
			print()
			if("results" in intervals.keys()):
				periods = intervals["results"]
				for period in periods:
					
					print(period["from"],"until",period["to"])
					
					keyphrases = period["keyphrases"]
					for keyphrase in keyphrases:
						if(verbose):
							print("\t",keyphrase.headlines[0].info.datetime.date(), "[", keyphrase.headlines[0].info.domain, "]", keyphrase.kw)
						else:
							print("\t" + keyphrase.kw)
					
					print()

			n_domains = len(intervals["domains"])
			n_docs = intervals["stats"]["n_docs"]

		print()
		print("Summary")
		print("\tNumber of unique domains",n_domains)
		print("\tFound documents",n_docs)

		
			
		
