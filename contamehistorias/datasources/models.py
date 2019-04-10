# -*- coding: utf-8 -*-
from datetime import datetime
import json
from .utils import *

class BaseDataSource(object):

	def __init__(self, name):
		self.name = name

	def getResult(self, query, **kwargs):
		raise NotImplementedError('getResult on ' + self.name + ' not implemented yet!')

	def toStr(self, list_of_headlines_obj):
		return json.dumps(list(map(lambda obj: obj.encoder(), list_of_headlines_obj)))

	def toObj(self, list_of_headlines_str):
		return [ ResultHeadLine.decoder(x) for x in json.loads(list_of_headlines_str) ]

class RoundTripEncoder(json.JSONEncoder):
	DATE_FORMAT = "%Y-%m-%d"
	TIME_FORMAT = "%H:%M:%S"
	def default(self, obj):
		if isinstance(obj, datetime):
			return obj.strftime("%s %s" % (self.DATE_FORMAT, self.TIME_FORMAT))
		return super(RoundTripEncoder, self).default(obj)

class ResultHeadLine(object):

	def __init__(self, headline, datetime, domain, url):
		self.headline = headline
		self.datetime = datetime
		self.domain = domain
		self.url = url

	@classmethod
	def decoder(cls, json_str):
		json_obj = json.loads(json_str)
		return cls(headline = json_obj['headline'], datetime=datetime.strptime(json_obj['datetime'], "%s %s" % (RoundTripEncoder.DATE_FORMAT, RoundTripEncoder.TIME_FORMAT)), domain = json_obj['domain'], url = json_obj['url'])
	
	def encoder(self):
		return json.dumps(self.__dict__, cls=RoundTripEncoder)