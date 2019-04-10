# Conta-me Historias Temporal Summarization
This package can retrive articles from Arquivo.pt web archive and produce a temporal summarization.

## Install
Requires Python 3

 ```bash
 pip install git+https://github.com/LIAAD/TemporalSummarizationFramework.git
 ```

## Using terminal

Accessing client help

```bash

> contamehistorias --help

Usage: contamehistorias [OPTIONS]

  Console script for tempsummarization.

Options:
  --query TEXT       Perform news retrieval with informed query
  --language TEXT    Expected language in headlines
  --start_date DATE  Perform news retrieval since this date
  --end_date DATE    Perform news retrieval until this date
  --domains TEXT     Comma separated list of domains
                     (www.publico.pt,www.dn.pt)
  --verbose
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

## Code Usage 

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

Computing important dates and selecting relevant keyphrases
  
```python 
  
  from contamehistorias import engine
  language = "pt"
  
  cont = contamehistorias.engine.TemporalSummarizationEngine()
  intervals = cont.build_intervals(search_result, language)
  
  cont.pprint(intervals)
	  
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

## Serialization
Serializing results. Useful for caching.

### Serializing search results
 ```python
search_result = apt.getResult(query=query, **params)

# object to string
search_result_serialized = apt.toStr(search_result) 

# string to object
search_result = apt.toObj( search_result_serialized )
```
 
### Serializing summarization results
```python
import json

summ_result = conteme.build_intervals(search_result)

# object to string
summ_result_serialized = json.dumps(conteme.serialize(summ_result))

# string to object
summ_result = json.loads(str(summ_result_serialized))
```

## Extending 
You can extend it to use your own data source.  All you need to do is extend [BaseDataSource](contamehistorias/datasources/models.py) class. 
Take a look at the example using [BingNewsSearchAPI](contamehistorias/datasources/bing.py).
Method **getResult** must return list of object ResultHeadLine.

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

## NewsIR'16 dataset support
It is possible to test using (http://research.signalmedia.co/newsir16/signal-dataset.html). In this case there is no need to specify date interval since the dataset comprehends only a one month time frame. 

```
$ contamehistorias_signal --help
Usage: contamehistorias_signal [OPTIONS]


  Console script for tempsummarization.

Options:
  --query TEXT  Perform news retrieval with informed query
  --verbose

  --help        Show this message and exit.

```

## Contact
admin@contamehistorias.pt

Developed by researchers from Laboratório de Inteligência Artificial e Apoio a Decisão (LIAAD - INESCTEC), and affiliated to Instituto Politécnico de Tomar ; Universidade do Porto; Universidade de Kyoto
