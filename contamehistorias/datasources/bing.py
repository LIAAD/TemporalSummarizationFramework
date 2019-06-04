# -*- coding: utf-8 -*-
from .models import *
import requests
import time

class BingNewsSearchAPI(BaseDataSource):
	URL_REQUEST = 'https://api.cognitive.microsoft.com/bing/v7.0/news/search'
	
	def __init__(self, api_key, processes=4):
		BaseDataSource.__init__(self, 'BingNewsSearchAPI')
		self.api_key = api_key
		
		self.processes = processes		
		self.headers = {"Ocp-Apim-Subscription-Key" : api_key}
		self.max_documents = 2000

	def parse_news_article(self, item):
		
		pubdate = datetime.strptime(item["datePublished"].replace('.0000000Z',''), '%Y-%m-%dT%H:%M:%S')
		domain_name = item["provider"][0]["name"]

		result_item = ResultHeadLine(headline=item['name'], datetime=pubdate, domain=domain_name, url=item['url'])
		return result_item

	def getResult(self, query, **kwargs):
		
		params  = {"q": query, "count":"100", "mkt":"en-US"}
		
		headers = {"Ocp-Apim-Subscription-Key" : self.api_key}

		response = requests.get(BingNewsSearchAPI.URL_REQUEST, headers=headers, params=params)
		response.raise_for_status()
		search_results = response.json()

		base_search_query_url = search_results["readLink"]
		print(base_search_query_url)

		num_pages = int(search_results["totalEstimatedMatches"] / 100)
		print("num_pages",num_pages)
		page_size = 100

		#first page rows
		results = []		
		
		for article in search_results["value"]:
			results.append(self.parse_news_article(article))

		#next pages if available
		for page in range(0, num_pages + 1)[:200]:
			offset = page * page_size
			params["offset"] = offset
		
			#response = requests.get(search_url, headers=headers, params=params)
			print (base_search_query_url,"offset:"+str(offset))
		
			if(page % 3 == 0):
				print("sleep")
				time.sleep(0.5)
		
			response = requests.get(BingNewsSearchAPI.URL_REQUEST, headers=self.headers, params=params)
			response.raise_for_status()
			search_results = response.json()

			for article in search_results["value"]:
				results.append(self.parse_news_article(article))

			if(len(results) > self.max_documents ):
				
				break

		return results
