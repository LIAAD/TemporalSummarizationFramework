# -*- coding: utf-8 -*-

"""Console script for tempsummarization."""
import sys
from datetime import datetime
import click
from click_datetime import Datetime

from contamehistorias.engine import TemporalSummarizationEngine
from contamehistorias.datasources.mediacloud import MediaCloudSearchAPI

@click.command()
@click.option('--query', help="Perform news retrieval with informed query")
@click.option('--language',default="en", help="Expected language in headlines")
@click.option('--start_date', type=Datetime(format='%d/%m/%Y'), default=datetime(year=2010, month=1, day=1), help="Perform news retrieval since this date")
@click.option('--end_date', type=Datetime(format='%d/%m/%Y'), default=datetime.now(), help="Perform news retrieval until this date")
@click.option('--api_key', help="MediaCloud API key")
@click.option('--verbose', is_flag=True)
def main(query, language, start_date, end_date, api_key, verbose):
    """Console script for tempsummarization."""
    
    click.echo("Conta-me Historias Temporal Summarization. Media Cloud API example (more info at https://mediacloud.org/)")
    print("--query",query)
    print("--language",language)
    print("--start_date",start_date)
    print("--end_date",end_date)
    
    print()
    
    params = {  'language':language,
                'start_date':start_date, 
                'end_date':end_date }

    click.echo("Performing search. This may take a while.")
    search_result = MediaCloudSearchAPI(api_key=api_key).getResult(query=query, **params)

    click.echo("Computing temporal summarization ...")
    engine = TemporalSummarizationEngine()
    summary_result = engine.build_intervals(search_result, language)

    engine.pprint(summary_result, verbose)
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 