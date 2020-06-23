# Arxiv Scraper

This is a small program which will grab all the papers posted on the arxiv each day, convert them to pure text, and, in each of them, search for the regular expressions listed in the configuration file. 

## Installation

First install the required dependencies:

```
$ pip install arxiv dateutil slate3k
```

Then clone this repository

```
$ git clone https://github.com/bfichera/arxivscraper
```

## Usage

Just run

```
$ python arxivscraper.py --config-file /path/to/my/config/file
```

## Configuration

See ``example_config.json``.
