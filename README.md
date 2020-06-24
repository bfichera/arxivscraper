# Arxiv Scraper

This is a small program which will grab all the papers posted in the last day, convert them to pure text, and, in each of them, search for the regular expressions listed in the configuration file. 

## Installation

First install the required dependencies:

```
$ pip install arxiv dateutil slate3k
```

Then clone this repository

```
$ git clone https://github.com/bfichera/arxivscraper
```

Finally, make a file called ``conf.py`` in the base directory with your configuration details. See ``example_conf.py``.

## Usage

Just run

```
$ python arxivscraper.py --config-file /path/to/my/config/file
```

## Configuration

See ``example_conf.py``. The search terms which are chemical formulas should go into the ``chem_terms`` field, with spaces between elements; they will be converted to a regular expression which I've found matches well most of the time (different authors like to format TaS<sub>2</sub> like ``TaS2``, ``TaS$_2$``, ``TaS$_{2}$``, etc. and the ``chem_terms`` tries to catch all of them). Otherwise, use the ``terms`` field.
