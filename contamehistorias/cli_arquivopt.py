# -*- coding: utf-8 -*-

"""Console script for tempsummarization."""
import sys
from datetime import datetime
import click
from click_datetime import Datetime

from contamehistorias.engine import TemporalSummarizationEngine
from contamehistorias.datasources.webarchive import ArquivoPT

import contamehistorias, os

@click.command()
@click.option('--query', help="Perform news retrieval with informed query")
@click.option('--language',default="pt", help="Expected language in headlines")
@click.option('--start_date', type=Datetime(format='%d/%m/%Y'), default=datetime(year=2010, month=1, day=1), help="Perform news retrieval since this date")
@click.option('--end_date', type=Datetime(format='%d/%m/%Y'), default=datetime.now(), help="Perform news retrieval until this date")
@click.option('--domains', help="Comma separated list of domains (www.publico.pt,www.dn.pt)")
@click.option('--verbose', is_flag=True)
def main(query, domains, language, start_date, end_date, verbose):
    """Console script for temporal summarization."""

    click.echo("Conta-me Historias Temporal Summarization. Based on Arquivo.pt API (more info at http://arquivo.pt/)")
    print("--query",query)
    print("--start_date",start_date)
    print("--end_date",end_date)
    print("--language",language)
        
    print()

    params = { 'from':start_date, 
               'to':end_date}
    
    #if domain list not specified, load default domain list 
    if not(domains):        
        templates_dir = os.path.dirname(contamehistorias.__file__)
        template_file = os.path.join(templates_dir, "domains.txt")
        params['domains'] = open(template_file,"r").readlines()
    else:
        params['domains'] = domains.split(",")

    click.echo("Performing search. This may take a while.")
    search_result = ArquivoPT().getResult(query=query, **params)

    click.echo("Computing temporal summarization ...")
    engine = TemporalSummarizationEngine()
    summary_result = engine.build_intervals(search_result, language)

    engine.pprint(summary_result, verbose)
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 