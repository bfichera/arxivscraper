import arxiv
from datetime import datetime
import logging
import argparse
from dateutil.parser import parse
import requests
import io
import re
import json
import smtplib
import ssl
import slate3k as slate

_logger = logging.getLogger(__name__)


def send_email(cfg, matches):
    message = ''
    message += 'From: '+cfg['from_email']+'\n'
    message += 'To: '+cfg['to_email']+'\n'
    message += 'Subject: Important arxiv post(s)\n\n'
    for regex, ids in matches.items():
        if ids:
            message += f'Matches for regex {regex}\n'
            for id_ in ids:
                message += '    '
                message += str(id_)
                message += '\n'
    
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(
        cfg['smtp_server'],
        cfg['port'],
        context=context,
    ) as server:
        server.login(
            cfg['from_email'],
            cfg['password'],
        )
        server.sendmail(
            cfg['from_email'],
            cfg['to_email'],
            message,
        )
            

def posted_today(paper, date=datetime.today()):
    paper_published = parse(paper.published)
    if date.date() == paper_published.date():
        return True
    return False


def get_pdf_text(url):
    fr = io.BytesIO(requests.get(url).content)
    text = slate.PDF(fr)
    return str(text)


def in_pdf(url, list_of_regex, flags=0):
    text = get_pdf_text(url)
    answers = {regex:False for regex in list_of_regex}
    for regex in list_of_regex:
        prog = re.compile(regex, flags)
        result = prog.search(text)
        if result is not None:
            answers[regex] = True
    return answers


def sanitize_chem_term(chem_term):
    legal = r'(\s|\$|_|\{|\})*'
    chem_list = chem_term.split(' ')
    for i,element in enumerate(chem_list):
        head = element.rstrip('123456789')
        tail = element[len(head):]
        if tail != '':
            head = head + legal
            tail = tail + legal
        chem_list[i] = head+tail
    return r'\s*'.join(chem_list)
            

def main(cfg):

    ##
    ## Make terms list
    ##
    terms = cfg['terms']
    for chem_term in cfg['chem_terms']:
        terms.append(sanitize_chem_term(chem_term))

    query_terms = [
        'cat:'+cfg['section'],
    ]
    results = arxiv.query(
        query=' AND '.join(query_terms),
        sort_by='submittedDate',
        start=0,
        max_results=cfg['max_results'],
        sort_order='descending',
        iterative=True,
    )
    today_results = (
        p for p in results() 
        if posted_today(p, datetime(2020, 6, 19))
    )

    matches = {}
    flagsdict = {
        'IGNORECASE': re.IGNORECASE,
        'MULTILINE': re.MULTILINE,
        'DOTALL': re.DOTALL,
        'UNICODE': re.UNICODE,
        'LOCALE': re.LOCALE,
        'VERBOSE': re.VERBOSE,
    }
    flags = [flagsdict[flag.upper()] for flag in cfg['flags']]
    for paper in today_results:
        try:
            logging.info(f'Checking {paper.id}...')
            for regex, is_in in in_pdf(
                paper.pdf_url,
                terms,
                flags=flags,
            ).items():
                if is_in:
                    if regex not in matches.keys():
                        matches[regex] = [paper.id]
                    else:
                        matches[regex].append(paper.id)
                    
        except:
            pass

    send_email(cfg, matches)


def get_cfg():

    from runpy import run_path

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--config-file',
        type=str,
        dest='config_file',
        required=True,
    )
    args = parser.parse_args()

    cfg = run_path(args.config_file)['cfg']
    return cfg


if __name__ == '__main__':
    cfg = get_cfg()
    main(cfg)
