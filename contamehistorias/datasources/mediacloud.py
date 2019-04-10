# -*- coding: utf-8 -*-
from .models import *
from .utils import *

import mediacloud
import json
import dateutil.relativedelta
from datetime import datetime
from urllib.parse import urlparse

class MediaCloudSearchAPI(BaseDataSource):
	
	def __init__(self, api_key):
		BaseDataSource.__init__(self, 'MediaCloudSearchAPI')
		self.api_key = api_key
		
	def getResult(self, query, **kwargs):
		
		if not(self.api_key):
			raise ValueError("Please specify API key")

		self.mc = mediacloud.api.MediaCloud(self.api_key)
		
		start_date = None
		end_date = None

		if('end_date') in kwargs.keys():
			end_date = kwargs['end_date']
		else:
			#today
			end_date = datetime.now().date()

		if('start_date') in kwargs.keys():
			start_date = kwargs['start_date']
		else:
			#1 month
			start_date = end_date - dateutil.relativedelta.relativedelta(months=12)

		language = "en"
		if("language" in kwargs.keys()):
			language = kwargs["language"].strip()

		fetch_size = 500
		stories = []
		last_processed_stories_id = 0
		
		while len(stories) < 5000:
			fetched_stories = self.mc.storyList(query +' AND (language:'+language+')', 
										solr_filter=self.mc.publish_date_query(start_date, end_date),
										last_processed_stories_id=last_processed_stories_id, 
										rows= fetch_size)

			stories.extend(fetched_stories)
			if len( fetched_stories) < fetch_size:
				break
			
			last_processed_stories_id = stories[-1]['processed_stories_id']
		
		result = []
		for item in stories:
			
			title = item["title"]
			title = title.replace("[","").replace("]","").replace("&quot;","").replace("\""," ")

			pubdate = datetime.strptime(item["publish_date"], '%Y-%m-%d %H:%M:%S')
			domain = urlparse(item["media_url"]).netloc
			
			result_item = ResultHeadLine(headline=title, datetime=pubdate, domain=domain, url=item["url"])
			result.append(result_item)

		
		return result		