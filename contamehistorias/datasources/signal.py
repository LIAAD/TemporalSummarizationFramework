# -*- coding: utf-8 -*-
from .models import *
from .utils import *

from datetime import datetime
import requests

class SignalNewsIRDataset(BaseDataSource):
	URL_REQUEST = 'http://194.117.29.148/solr/signalnews-articles/select'
	
	def __init__(self, processes=4):
		BaseDataSource.__init__(self, 'SignalNewsIRDataset')
		self.processes = processes

	def getResult(self, query, **kwargs):
		
		params = {
			'q':'title:(%s) OR content:(%s)' % (query, query),
			'rows':2000,		
			'fl': 'source,title,published'
		}

		response = requests.get(SignalNewsIRDataset.URL_REQUEST, params=params)
		if response.status_code != 200:
			return None

		response_json = response.json()
		results = []

		for item in response_json['response']['docs']:

			if not (item['title'][0]):
				continue
			
			domain_url = item["source"][0]
			pubdate = datetime.strptime(item["published"][0], '%Y-%m-%dT%H:%M:%SZ')
			title = item['title'][0]

			item_result = ResultHeadLine(headline=title, datetime=pubdate, domain=domain_url, url="")
			
			results.append( item_result )

		return results
