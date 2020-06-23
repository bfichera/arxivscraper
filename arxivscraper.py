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


def in_pdf(url, list_of_regex):
    text = get_pdf_text(url)
    answers = {regex:False for regex in list_of_regex}
    for regex in list_of_regex:
        prog = re.compile(regex)
        result = prog.search(text)
        if result is not None:
            answers[regex] = True
    return answers
            

def main(cfg):

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
    for paper in today_results:
        try:
            logging.info(f'Checking {paper.id}...')
            for regex, is_in in in_pdf(
                paper.pdf_url, cfg['terms']
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

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--config-file',
        type=str,
        dest='config_file',
        required=True,
    )
    args = parser.parse_args()

    with open(args.config_file, 'r') as fh:
        cfg = json.load(fh)

    return cfg


if __name__ == '__main__':
    cfg = get_cfg()
    main(cfg)
