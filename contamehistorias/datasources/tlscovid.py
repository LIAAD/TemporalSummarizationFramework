
from urllib.parse import urljoin, urlparse
from datetime import datetime
import requests
import json

from elasticsearch import Elasticsearch, helpers


class RoundTripEncoder(json.JSONEncoder):
    DATE_FORMAT = "%Y-%m-%d"
    TIME_FORMAT = "%H:%M:%S"

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime("%s %s" % (self.DATE_FORMAT, self.TIME_FORMAT))
        return super(RoundTripEncoder, self).default(obj)


class ResultHeadLine(object):
    def __init__(self, headline, datetime, title, domain, url, is_km=False):
        self.headline = headline
        self.datetime = datetime
        self.title = title
        self.domain = domain
        self.url = url
        self.is_km = is_km

    @classmethod
    def decoder(cls, json_str):
        json_obj = json.loads(json_str)
        return cls(headline=json_obj['headline'], datetime=datetime.strptime(json_obj['datetime'], "%s %s" % (RoundTripEncoder.DATE_FORMAT, RoundTripEncoder.TIME_FORMAT)), title=json_obj['title'], domain=json_obj['domain'], url=json_obj['url'], is_km=json_obj['is_km'])

    def encoder(self):
        return json.dumps(self.__dict__, cls=RoundTripEncoder)


class SearchEngine(object):
    def __init__(self, name):
        self.name = name

    def getResult(self, query, **kwargs):
        raise NotImplementedError(
            'getResult on ' + self.name + ' not implemented yet!')

    def toStr(self, list_of_headlines_obj):
        return json.dumps(list(map(lambda obj: obj.encoder(), list_of_headlines_obj)))

    def toObj(self, list_of_headlines_str):
        return [ResultHeadLine.decoder(x) for x in json.loads(list_of_headlines_str)]


class ElasticSearchCovid(SearchEngine):

    URL_ELASTICSEARCH = 'http://localhost:9200/'

    es = Elasticsearch(URL_ELASTICSEARCH)

    INPUT_FORMAT = '%Y-%m-%d'

    def __init__(self):
        SearchEngine.__init__(self, 'ElasticSearchCovid')

    def getResult(self, query, **kwargs):

        # kwargs must include index, and optionally a list of sources

        index = kwargs.get('index')

        if 'sources' in kwargs:
            sources = kwargs.get('sources')
        else:
            sources = []

        # Check if query is in topics
        topics = self.get_topics()
        index_topics = [t['topic'] for t in topics if t['lan'] == index]

        is_topic = query in index_topics

        if not sources:
            es_response = self.get_documents_from_query_by_index(
                index, query, is_topic)
        else:
            es_response = self.get_documents_from_query_by_sources(
                index, query, sources, is_topic)

        search_results = list(es_response)

        result = []
        for item in search_results:

            item = item["_source"]

            domain = urlparse(item['url']).netloc

            # If query is topic there is a ground-truth timeline. Mark news accordingly if it is key moment or not.
            if is_topic:
                item_result = ResultHeadLine(headline=item['news'], datetime=datetime.strptime(
                    item['date'], self.INPUT_FORMAT), title=item['title'], domain=domain, url=item['url'], is_km=item['is_km'])
            # If query is not topic there is not a ground-truth timeline so do not mark any news as key moment.
            else:
                item_result = ResultHeadLine(headline=item['news'], datetime=datetime.strptime(
                    item['date'], self.INPUT_FORMAT), title=item['title'], domain=domain, url=item['url'], is_km=False)

            result.append(item_result)

        print('Is topic:', str(is_topic))
        print('Number of liveblog news:', str(len(result)))

        if is_topic:
            if not sources:
                km_count = self.get_keymoments_count_by_index(index, query)
            else:
                km_count = self.get_keymoments_count_by_sources(
                    index, query, sources)

            print('Number of key moments:', str(km_count))

        return result

    def get_documents_from_query_by_index(self, index, query, is_topic):

        if is_topic:
            query_body = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "match": {
                                    "topic.keyword": query
                                }
                            }
                        ]
                    }
                }
            }
        else:
            query_body = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "match": {
                                    "news": query
                                }
                            }
                        ]
                    }
                }
            }

        # Query Elasticsearch
        es_response = helpers.scan(
            self.es,
            index=index,
            query=query_body
        )

        return es_response

    def get_documents_from_query_by_sources(self, index, query, sources, is_topic):

        if is_topic:
            query_body = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "match": {
                                    "topic.keyword": query
                                }
                            },
                            {
                                "terms": {
                                    "source": sources
                                }
                            }
                        ]
                    }
                }
            }
        else:
            query_body = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "match": {
                                    "news": query
                                }
                            },
                            {
                                "terms": {
                                    "source": sources
                                }
                            }
                        ]
                    }
                }
            }

        # Query Elasticsearch
        es_response = helpers.scan(
            self.es,
            index=index,
            query=query_body
        )

        return es_response

    def get_keymoments_count_by_index(self, index, query):

        is_km = True

        query_body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "topic.keyword": query
                            }
                        },
                        {
                            "match": {
                                "is_km": is_km
                            }
                        }
                    ]
                }
            }
        }

        # Query Elasticsearch
        es_response = self.es.count(query_body, index)

        km_count = es_response['count']

        return km_count

    def get_keymoments_count_by_sources(self, index, query, sources):

        is_km = True

        query_body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "topic.keyword": query
                            }
                        },
                        {
                            "match": {
                                "is_km": is_km
                            }
                        },
                        {
                            "terms": {
                                "source": sources
                            }
                        }
                    ]
                }
            }
        }

        # Query Elasticsearch
        es_response = self.es.count(query_body, index)

        km_count = es_response['count']

        return km_count

    def get_all_indices(self):

        # Ingore kibana indices
        cat_idx = '_cat/indices/*,-.*?format=json'

        es_indices_api_endpoint = urljoin(
            self.URL_ELASTICSEARCH, cat_idx)

        # Query Elasticsearch
        response = requests.get(es_indices_api_endpoint)

        indices = [r['index']
                   for r in response.json() if r['index'] != 'topics']

        return indices

    def get_topics(self):

        # Query Elasticsearch
        es_response = helpers.scan(
            self.es,
            index='topics',
            query={"query": {"match_all": {}}}
        )

        topics = [t['_source'] for t in es_response]

        return topics

    def get_topic_key_moments_by_index(self, index, topic):

        is_km = True

        query_body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "topic.keyword": topic
                            }
                        },
                        {
                            "match": {
                                "is_km": is_km
                            }
                        }
                    ]
                }
            }
        }

        # Query Elasticsearch
        es_response = helpers.scan(
            self.es,
            index=index,
            query=query_body
        )

        # {'date_x': [list_of_news], 'date_y': [list_of_news], ...}
        topic_key_moments = {}
        for item in es_response:

            item = item['_source']

            news_body = item['news']
            news_date = item['date']

            if news_date in topic_key_moments:
                topic_key_moments[news_date].append(news_body)
            else:
                topic_key_moments[news_date] = [news_body]

        return topic_key_moments

    def get_documents_from_query_by_sources_in_date_range(self, index, query, sources, start_date, end_date):

        query_body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "topic.keyword": query
                            }
                        },
                        {
                            "terms": {
                                "source": sources
                            }
                        },
                        {
                            "range": {
                                "date": {
                                    "gte": datetime.strptime(start_date, "%Y-%m-%d"),
                                    "lte": datetime.strptime(end_date, "%Y-%m-%d")
                                }
                            }
                        }
                    ]
                }
            }
        }

        # Query Elasticsearch
        es_response = helpers.scan(
            self.es,
            index=index,
            query=query_body
        )

        return list(es_response)

    def get_key_moments_from_query_by_sources_in_date_range(self, index, query, sources, start_date, end_date):
        
        is_km = True

        query_body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "topic.keyword": query
                            }
                        },
                        {
                            "terms": {
                                "source": sources
                            }
                        },
                        {
                            "range": {
                                "date": {
                                    "gte": datetime.strptime(start_date, "%Y-%m-%d"),
                                    "lte": datetime.strptime(end_date, "%Y-%m-%d")
                                }
                            }
                        },
                        {
                            "match": {
                                "is_km": is_km
                            }
                        }
                    ]
                }
            }
        }

        # Query Elasticsearch
        es_response = helpers.scan(
            self.es,
            index=index,
            query=query_body
        )
        
        return list(es_response)
