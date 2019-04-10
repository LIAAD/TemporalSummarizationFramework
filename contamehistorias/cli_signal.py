# -*- coding: utf-8 -*-

"""Console script for tempsummarization."""
import sys
from datetime import datetime
import click
from click_datetime import Datetime

from contamehistorias.engine import TemporalSummarizationEngine
from contamehistorias.datasources.signal import SignalNewsIRDataset

@click.command()
@click.option('--query', help="Perform news retrieval with informed query")
@click.option('--verbose', is_flag=True)
def main(query, verbose):
    """Console script for tempsummarization."""
    
    click.echo("Conta-me Historias Temporal Summarization. Signal NewsIR'16 dataset example (more info http://research.signalmedia.co/newsir16/signal-dataset.html")
    print("--query",query)
    
    print()
    
    click.echo("Performing search. This may take a while.")
    search_result = SignalNewsIRDataset().getResult(query=query)

    click.echo("Computing temporal summarization ...")
    engine = TemporalSummarizationEngine()
    summary_result = engine.build_intervals(search_result, "en")

    engine.pprint(summary_result, verbose)
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 