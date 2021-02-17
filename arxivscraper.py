from datetime import datetime
from datetime import timedelta
import logging
import argparse
import requests
import io
import re
import smtplib
import ssl
from functools import reduce
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import arxiv
import slate3k as slate
from dateutil.parser import parse
from timeout_decorator import (
    timeout,
    TimeoutError,
)
    

_logger = logging.getLogger(__name__)


def send_email(cfg, matches, errors):
    # Create the message 
    message = MIMEMultipart('alternative')
    message['From'] = cfg['from_email']
    message['To'] = cfg['to_email']
    message['Subject'] = 'Important arxiv post(s)'
    text = ''
    html = '<html>\n'
    html += '<body>\n'
    for regex, papers in matches.items():
        if papers:
            text += f'Matches for regex {regex}\n'
            html += f'<p>\nMatches for regex {regex}\n<ul>\n'
            for paper in papers:
                text += f'    {str(paper.id)}\n'
                html += f'<li><a href="{str(paper.id)}">{str(paper.title)}</a></li>\n'
            html += '</ul>\n</p>\n'
    text += f'There were {len(errors)} errors.\n'
    html += f'There were {len(errors)} errors.<br>\n'
    for error in errors:
        text += error
        text += '\n'
        html += error+'<br>'
    html += '</body>'
    html += '</html>'

    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    message.attach(part1)
    message.attach(part2)
    
    # Actually send the email
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
            message.as_string(),
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
        if posted_today(p, datetime.today()-timedelta(days=1))
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

    @timeout(cfg['timeout'])
    def in_pdf(url, list_of_regex, flags=0):
        text = get_pdf_text(url)
        answers = {regex:False for regex in list_of_regex}
        for regex in list_of_regex:
            prog = re.compile(regex, flags)
            result = prog.search(text)
            if result is not None:
                answers[regex] = True
        return answers

    errors = []
    for paper in today_results:
        try:
            _logger.info(f'Checking {paper.id}...')
            for regex, is_in in in_pdf(
                paper.pdf_url,
                terms,
                flags=reduce(int.__or__, flags),
            ).items():
                if is_in:
                    if regex not in matches.keys():
                        matches[regex] = [paper]
                    else:
                        matches[regex].append(paper)
                    
        except Exception as exception:
            if isinstance(exception, TimeoutError):
                msg = f'PDF reader timeout reached for {paper.id}.'
                _logger.warning(msg)
            else:
                msg = str(exception)+f' called for {paper.id}.'
            errors.append(msg)
                
    if matches:
        send_email(cfg, matches, errors)

    if errors:
        _logger.warning('There were PDF errors.')
        for error in errors:
            _logger.warning(error)


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
