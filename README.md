# Conta-me Historias Temporal Summarization
Conta-me Histórias / Tell me Stories is a temporal summarization framework of news articles that allows users to explore and revisit events in the past. Built on top of the Portuguese web archive [http://arquivo.pt], it can be extended to support different datasets, including traditional media such as Reuters, Bloomberg, etc. Unlike, the Portuguese version (which runs on top of the Portuguese Web Archive), the English version of this App uses Bing News Search API to create narratives.

## Contributions
During the last decade, we have been witnessing an ever-growing number of online contents posing new challenges for those who aim to understand a given event. This exponential growth of the volume of data, together with the phenomenon of media bias, fake news and filter bubbles, has contributed to the creation of new challenges in information access and transparency. One possible approach to overcome this problem is to automatically summarize large amount of news into consistent narratives. Tell me Stories emerges in this context, as an important contribution for anyone interested in having access to the overall picture of a given event in a quick manner. Our project may be considered as an additional solution that allows the general public (students, journalists, politics, researchers, etc) to better explore any kind of data that has been covered by the media. 

## How does it works?
Tell me Stories collects information from web archives (such as the Arquivo.pt) or media outlets (such as Reuters, Bloomberg or Bing News) and provides a full-text search service that enables the retrieval of past (to present) information. To select relevant stories of different time-periods, we rely on YAKE! [http://yake.inesctec.pt] a keyword extraction algorithm developed by our research team, which selects the most important excerpts (namely text titles) of a topic over time, to present to the user.

## Where can I find Conta-me Histórias/Tell me Stories?
Tell me Stories is available online [http://contamehistorias.pt; http://tellmestories.pt], on [Google Play](https://play.google.com/store/apps/details?id=com.app.projetofinal), as an open source Python package [https://github.com/LIAAD/TemporalSummarizationFramework] and as an [API](http://contamehistorias.inesctec.pt/arquivopt/apidocs#/default/get_api_v1_search).

## Install
Requires Python 3

 ```bash
 pip install git+https://github.com/LIAAD/TemporalSummarizationFramework.git
 ```

## Usage (Python)

### Obtain Results from Arquivo.pt
Using ArquivoPT search engine API as datasource.
  
```python  
  from contamehistorias.datasources.webarchive import ArquivoPT
  from datetime import datetime
  
# Specify website and time frame to restrict your query
  domains = [ 'http://publico.pt/', 'http://www.rtp.pt/',
  			  'http://www.dn.pt/', 'http://news.google.pt/',]

  params = { 'domains':domains, 
            'from':datetime(year=2016, month=3, day=1), 
            'to':datetime(year=2018, month=1, day=10) }
  
  query = 'Dilma Rousseff'
  
  apt =  ArquivoPT()
  search_result = apt.getResult(query=query, **params)
```  

### Iterate over the results obtained from Arquivo.pt
"search_result" object belongs to the "contamehistorias.datasources.models.ResultHeadLine" class and returns the "raw" results from the Arquivo.pt API.

```python
#Total number of results retrieved by Arquivo.pt
len(search_result)
```

Iterate over the entire set of retrieved results:
```python
for x in search_result:
    print(x.datetime)
    print(x.domain)
    print(x.headline)
    print(x.url)
    print()
```

### Computing important dates and selecting relevant keyphrases/headlines
  
```python 
  
from contamehistorias import engine
language = "pt"
  
cont = engine.TemporalSummarizationEngine()
summ_result = cont.build_intervals(search_result, language)
  
cont.pprint(summ_result)
	  
``` 
Output
``` 
-------------------------
2016-03-01 01:22:06 until 2016-03-26 07:03:42
	 líder da maior associação patronal do brasil pede saída de dilma rousseff
	 começou processo de impeachment de dilma rousseff
	 dilma rousseff foi a casa de lula da silva oferecer solidariedade
	 milhares de pessoas saem à rua contra governo de dilma rousseff
	 milhares saem à rua exigindo demissão da presidente brasileira dilma rousseff
	 sociedade civil exige na rua demissão de dilma rousseff
	 manifestações pressionam dilma rousseff para deixar a presidência
	 milhares protestam contra governo de dilma rousseff no brasil
	 lula já terá aceitado ser ministro de dilma rousseff
	 presidente brasileira confirma entrada de lula da silva para o seu governo
	 lula da silva é ministro de dilma
	 lula da silva toma posse como ministro de dilma
	 dilma rousseff renuncia ao cargo ao nomear lula da silva
	 partido do ministro do desporto abandona governo de dilma rousseff
	 oposição a dilma pede destituição do novo ministro da justiça
	 comissão especial vai analisar a destituição de dilma rousseff
	 gregório duvivier escreve em exclusivo para a sábado sobre dilma e lula
-------------------------
2016-03-27 04:23:41 until 2016-05-04 07:10:13
	 parceiro de coligação deixa governo de dilma rousseff
	 juiz pede desculpa por divulgar escutas de dilma e lula
	 pmdb oficializa saída do governo de dilma rousseff
	 lula da silva apoia dilma rousseff através do facebook
	 lula defende dilma em vídeo no facebook
	 lula espera que supremo tribunal autorize a sua entrada no governo brasileiro
	 josé sócrates diz que destituição de dilma é um golpe político
	 comissão do impeachment aprova parecer favorável à destituição de dilma rousseff
	 advogado do governo vê irregularidades em parecer favorável à destituição de dilma
	 deputados aprovam relatório que propõe impeachment de dilma
	 aprovado relatório que propõe a destituição de dilma rousseff
	 comissão parlamentar aprova processo de destituição de dilma rousseff
	 pedido de destituição de dilma rousseff aquece congresso brasileiro
	 câmara dos deputados vota pedido de afastamento de dilma
	 câmara dos deputados aprova impeachment de dilma rousseff
	 parlamento do brasil aprova destituição de dilma
	 temer assume presidência enquanto rousseff procura apoios na onu
	 nicolás maduro sai em defesa de dilma rousseff
	 senado brasileiro aprovou nomes dos parlamentares que vão analisar destituição de dilma
	 processo de impeachment de dilma já está na comissão especial no senado

 ``` 

## Iterate over response
"summ_result" is a dictionary with 3 keys (`stats`, `domains`, `results`). "stats" is itself a dictionary; "domains" is a list and "results" is a list with several elements (namely dictionaries with detailed results).

### stats
"stats" is a dictionary consisting of 4 keys.

```python
summ_result["stats"]
```

### Domains
Domains keeps the list of URIs in the search.

 ```python
 summ_result["domains"]
 ```

### Results
summ_result ["results"] is a list that will have as many elements as there are relevant periods. Each of these relevant periods has a dictionary "from" (date) "to" (date) which enables to delimit the boundaries of the time-frame. Each time-period, in turn, has a number of keyphrases/headlines and corresponding information such as, the headline itself, its publication datetime (that is, the date when the webpage was collected by the Arquivo.pt), it's domain and URL.

 ```python
summ_result = cont.build_intervals(search_result, language)

for period in summ_result["results"]:
    
    print("--------------------------------")
    print(period["from"],"until",period["to"])
    
    # selected keyphrases
    keyphrases = period["keyphrases"]
    
    for keyphrase in keyphrases:
        print(keyphrase.kw)
        
        # sources
        for headline in keyphrase.headlines:
            print("Date", headline.info.datetime)
            print("Source", headline.info.domain)
            print("Url", headline.info.url)
            
        print()  
		
 ```

In case you want to have information about the score of the terms that compose the headline, please run the following code:
 ```python
 for period in summ_result["results"]:
       
    print("--------------------------------")
    print(period["from"],"until",period["to"])
   
    # selected headlines
    keyphrases = period["keyphrases"]
    
    for keyphrase in keyphrases:
        print("headline = " + keyphrase.kw)
        
       
        # sources
        for headline in keyphrase.headlines:
            print("Date", headline.info.datetime)
            print("Source", headline.info.domain)
            print("Url", headline.info.url)
            print("Headline completa = ", headline.info.headline)
        
        #Permite imprimir a importância de cada termo que faz parte da headline
        for termos in keyphrase.cand_obj.terms:
            print(f'{termos.unique_term} {termos.H}')
           
        print() 
 ```
 
## Serialization
Serializing results. Useful for caching.

### Serializing search results obtained from Arquivo.pt API
 ```python
from contamehistorias.datasources.webarchive import ArquivoPT
from datetime import datetime

# Specify website and time frame to restrict your query
domains = [ 'http://publico.pt/', 'http://www.rtp.pt/', 'http://www.dn.pt/', 'http://news.google.pt/',]

params = { 'domains':domains, 'from':datetime(year=2016, month=3, day=1), 'to':datetime(year=2018, month=1, day=10) }
  
query = 'Dilma Rousseff'
  
apt =  ArquivoPT()
search_result = apt.getResult(query=query, **params)

import json

# object to string
search_result_serialized = apt.toStr(search_result)

# string to object
search_result = apt.toObj( search_result_serialized )

print(search_result_serialized)
```
 
### Serializing summarization results
```python
from contamehistorias import engine
import datetime
language = "pt"
  
cont = engine.TemporalSummarizationEngine()
summ_result = cont.build_intervals(search_result, language)
 
import json

# object to string
summ_result_serialized = json.dumps(cont.serialize(summ_result))

# string to object
summ_result = json.loads(str(summ_result_serialized))
```

```python
print(summ_result_serialized)
```

```python
print(summ_result)
```

## Extending 
You can extend Tell me Stories to use your own data source. All you need to do is to extend [BaseDataSource](contamehistorias/datasources/models.py) class. See the below code for informative purposes (don't need to execute it):

```python
class BaseDataSource(object):

	def __init__(self, name):
		self.name = name

	def getResult(self, query, **kwargs):
		## must returl list of ResultHeadLine(headline, datetime, domain, url)
		raise NotImplementedError('getResult on ' + self.name + ' not implemented yet!')

	def toStr(self, list_of_headlines_obj):
		return json.dumps(list(map(lambda obj: obj.encoder(), list_of_headlines_obj)))

	def toObj(self, list_of_headlines_str):
		return [ ResultHeadLine.decoder(x) for x in json.loads(list_of_headlines_str) ]
```

Take a look at the example using the [SignalMedia dataset](contamehistorias/datasources/signal.py), which is indexed at a solr machine. Method **getResult** must return a list of object ResultHeadLine.
```python
from contamehistorias.datasources import models
from contamehistorias.datasources import utils
from datetime import datetime
import requests
class CustomSignalNewsIRDataset(models.BaseDataSource):
    URL_REQUEST = 'http://194.117.29.148/solr/signalnews-articles/select'
    
    def __init__(self, processes=4):
        models.BaseDataSource.__init__(self, 'SignalNewsIRDataset')
        self.processes = processes

    def getResult(self, query, **kwargs):

        params = {
            'q':'title:(%s) OR content:(%s)' % (query, query),
            'rows':2000,
            'fl': 'source,title,published'
        }

        response = requests.get(CustomSignalNewsIRDataset.URL_REQUEST, params=params)
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

            item_result = models.ResultHeadLine(headline=title, datetime=pubdate, domain=domain_url, url="")

            results.append( item_result )

        return results
```

Now run the following code to get the results:
```python
from contamehistorias.datasources import models
from contamehistorias import engine

language = "en"
query = "Donald Trump"

search_result = CustomSignalNewsIRDataset().getResult(query=query)

cont = engine.TemporalSummarizationEngine()
summ_result = cont.build_intervals(search_result, language)
  
cont.pprint(summ_result,True)
```
## NewsIR'16 dataset support
Given the previous code (which was shown for illustrative purposes) is already part of the package, you can use, instead, the following code to interact with the signal [media dataset](http://research.signalmedia.co/newsir16/signal-dataset.html) in a similar fashion as what was done for the Arquivo.pt API.  Note that given Signal media only covers one month no time-frame is specified.

```python
from contamehistorias.datasources.signal import SignalNewsIRDataset
from contamehistorias.engine import TemporalSummarizationEngine
from datetime import datetime
 
query = 'Dilma Rousseff'
language = 'en'

signal =  SignalNewsIRDataset()
search_result = signal.getResult(query=query)
```

Likewise the Arquivo.pt, one can interact with the raw results retrieved from the solr machine:
```python
len(search_result)
```

```python
for x in search_result:
    print(x.datetime)
    print(x.domain)
    print(x.headline)
    print(x.url)
    print()
```

As well as from the relevant headlines:
```python
cont = TemporalSummarizationEngine()
summ_result = cont.build_intervals(search_result, language)
  
cont.pprint(summ_result,True)
```

From the cli:
```
$ contamehistorias_signal --help
Usage: contamehistorias_signal [OPTIONS]


  Console script for tempsummarization.

Options:
  --query TEXT  Perform news retrieval with informed query
  --verbose

  --help        Show this message and exit.

```
## Bing
```python
from contamehistorias.datasources.bing import BingNewsSearchAPI
from contamehistorias.engine import TemporalSummarizationEngine
from datetime import datetime

language = "en"
query = 'Brexit'
key = "Introduce your KEY (from Microsoft Azure)"
  
bing =  BingNewsSearchAPI(key)
search_result = bing.getResult(query=query)
```

## Usage (Command Line)

Accessing client help

```bash
Usage: contamehistorias [OPTIONS]

Options:
  --query TEXT       Perform news retrieval with informed query
  --language TEXT    Expected language in headlines
  --start_date DATE  Perform news retrieval since this date
  --end_date DATE    Perform news retrieval until this date
  --domains TEXT     Comma separated list of domains (www.publico.pt,www.dn.pt)
  --verbose          Gets detailed information
  --help             Show this message and exit.
```

Running your query. You can specify start_date and end_date using date format (dd/mm/YYYY).

```bash
> contamehistorias --query "Donald Trump"


2010-04-12 16:37:09 until 2011-05-19 00:23:39
	filha de donald trump está grávida
	quanto vale donald trump
	donald trump deverá anunciar candidatura à casa branca

2011-07-19 16:24:20 until 2015-11-21 19:54:41
	donald trump vai apoiar mitt romney nas primárias
	multimilionário donald trump apoia candidatura de mitt romney
	multimilionário donald trump anuncia candidatura à corrida presidencial norte-americana

2015-11-22 19:02:15 until 2016-09-30 01:20:27
	donald trump quer proibir entrada de muçulmanos nos eua
	obama graceja sobre possível discurso do estado da união de donald trump
	deputados britânicos discutiram proibição de entrada donald trump no reino unido

2015-11-22 19:02:15 until 2016-09-30 01:20:27
	donald trump quer proibir entrada de muçulmanos nos eua
	obama graceja sobre possível discurso do estado da união de donald trump
	deputados britânicos discutiram proibição de entrada donald trump no reino unido
```

## Contact
arrp@inesctec.pt
vitordouzi@gmail.com
ricardo.campos@ipt.pt

Developed by researchers from Laboratório de Inteligência Artificial e Apoio a Decisão (LIAAD - INESCTEC), and affiliated to Instituto Politécnico de Tomar ; Universidade do Porto; Universidade de Kyoto

## Please cite the following works when using Conta-me Histórias/Tell me Stories
Pasquali, A., Mangaravite, V., Campos, R., Jorge, A., and Jatowt, A. (2019). Interactive System for Automatically Generating Temporal Narratives. In: Azzopardi L., Stein B., Fuhr N., Mayr P., Hauff C., Hiemstra D. (eds), Advances in Information Retrieval. ECIR'19 (Cologne, Germany. April 14 – 18). Lecture Notes in Computer Science, vol 11438, pp. 251 - 255. Springer. [pdf](https://link.springer.com/chapter/10.1007/978-3-030-15719-7_34)

## Awards
Conta-me Histórias / Tell me Stories won the Arquivo.pt 2018 contest [https://sobre.arquivo.pt/en/arquivo-pt-2018-award-winners/] and has been awarded the Best Demo Presentation at ECIR’19 [http://www.ecir2019.org].
