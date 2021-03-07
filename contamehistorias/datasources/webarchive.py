from .models import *
from .utils import *

import random
import time
from datetime import datetime
from collections import Counter, namedtuple
from multiprocessing import Pool
from itertools import repeat
from urllib.parse import urlparse
import requests, json
import re

class ArquivoPT(BaseDataSource):
	URL_REQUEST = 'http://arquivo.pt/textsearch'
	DATETIME_FORMAT = '%Y%m%d%H%M%S'
	
	def __init__(self, max_items_per_site=500, domains_by_request=2, processes=2, docs_per_query=1000):
		BaseDataSource.__init__(self, 'ArquivoPT')
		self.max_items_per_site = max_items_per_site
		self.domains_by_request = domains_by_request
		self.processes = processes
		self.docs_per_query = docs_per_query	
	
	def _select_text_to_keep(self, text, search_result, loc):
		# Whole match
		match = search_result.group(0)
		# Get original text without match
		without_match = text.replace(match, '')

		# This is an heuristic
		# Usually we are interested in the biggest string
		if len(match) > len(without_match):
			# This is the match without the noise delimiter
			if loc == 'beginning':
				text = search_result.group(1)
			elif loc == 'end':
				text = search_result.group(2)
		else:
			text = without_match
		
		return text

	def _pre_proc_title(self, text):

		# Remove soft hyphens
		text = text.replace('\xad', '')
		text = text.replace('\u00ad', '')

		# Titles come with noise in the beginning or end or in the begginig and end
		# Usually this noisy is delimited by chars like - | — > :

		# Regex to match noise in the beginning of titles
		regex_beg = re.compile(r'^([\"\w\s\/\']+)(-|—|\||>|:)\s', flags=re.UNICODE)

		search_result_beg = regex_beg.search(text)
		if search_result_beg:
			text = self._select_text_to_keep(text, search_result_beg, 'beginning')

		# Regex to match noise in the end of titles
		regex_end = re.compile(r'(-|—|\||>|\/)\s([\(\w\.\,\s\-\/\&\'\)]*)$', flags=re.UNICODE)

		search_result_end = regex_end.search(text)

		# Sometimes there is more than one noisy string at the end
		while search_result_end:
			text = self._select_text_to_keep(text, search_result_end, 'end')

			search_result_end = regex_end.search(text)
		
		return text

	def getResult(self, query, **kwargs):
		domains = kwargs['domains']
		
		if not(domains):
			raise ValueError('Empty domains list. You need to specify at least one site domain to restrict the search.')
			
		random.shuffle(domains)
		
		interval = ( kwargs['from'].strftime(ArquivoPT.DATETIME_FORMAT), kwargs['to'].strftime(ArquivoPT.DATETIME_FORMAT) )

		domains_chunks = [domains[i:i + min(self.domains_by_request, len(domains))] for i in range(0, len(domains), min(self.domains_by_request, len(domains)))]
		
		#run requests in parallel
		with Pool(processes=self.processes) as pool:
			results_by_domain = pool.starmap(self.getResultsByDomain, zip(domains_chunks, repeat(query), repeat(interval)))
		
		all_results = []
		for dominio_list in [ dominio_list for dominio_list in results_by_domain if dominio_list is not None ]:
			all_results.extend( dominio_list )

		return all_results

	def getResultsByDomain(self, domains, query, interval):

		itemsPerSite = min( self.max_items_per_site , int(2000/len(domains)))
		siteSearch = ','.join([urlparse(d).netloc for d in domains])

		params = {
			'q':query,
			'from':interval[0],
			'to':interval[1],
			'siteSearch':siteSearch,
			'maxItems':self.docs_per_query,
			'itemsPerSite':itemsPerSite,
			'type':'html',
			'fields': 'originalURL,title,tstamp,encoding,linkToArchive'
		}

		try:
			response = requests.get(ArquivoPT.URL_REQUEST, params=params, timeout=45)
			
		except:
			print('Timeout domains =', domains)
			return

		if response.status_code != 200:
			return

		json_obj = response.json()
		results = {}
		
		for item in json_obj['response_items']:
			if not (interval[0] < item['tstamp'] < interval[1]):
				continue

			url_domain = urlparse(item['originalURL']).netloc

			# Preprocess titles
			if 'Ã' in item['title']:
				item['title'] = multiple_replace(item['title'])

			item['title'] = self._pre_proc_title(item['title'])

			try:
				item_result = ResultHeadLine(headline=item['title'], 
											 datetime=datetime.strptime(item['tstamp'], ArquivoPT.DATETIME_FORMAT), 
											 domain=url_domain, 
											 url=item['linkToArchive'])

			except:
				#ignore entried with invalid date format
				pass

			if url_domain not in results:
				results[url_domain] = {}
			
			if item_result.url not in results[url_domain] or results[url_domain][item_result.url].datetime > item_result.datetime:
				results[url_domain][item_result.url] = item_result

		result_array = []
		for domain in results.values():
			result_array.extend( list(domain.values()) )

		return result_array