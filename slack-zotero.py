#!/usr/bin/env python

"""Simple interface between Slack Webhooks and Zotero API

   Intended to be used in a cron-like system that will periodically
   run this script with since=`last run's version` which can be
   obtained using the artifact parameter's functionality

   Example: slack-zotero.py --group 12345 \
                            --api "kjas734890fnlkjafFJnadsf" \
                            --webhook "https://hooks.slack.com/services/OUHAEFNF/OUIHAQEUN/uihsdf786SHBF6ebSF" \
                            --since 9043 \
                            --channel "#test" \
                            --username "Zotero Bot" \
                            --icon ":cow:" \
                            --artifact "slack-zotero-bot-previous.json" \
                            -v
"""

import urllib.request
import json
import requests
import re
import html
import time
import datetime
import sys


def retrieve_articles(group_id, api_key, limit=1, include='data', since=0):
    """Retrieves articles from a Zotero group API feed"""
    zotero_template = "https://api.zotero.org/groups/{group_id}/items/top?start=0&limit={limit}&format=json&v=3&key={api_key}"
    zotero_url = zotero_template.format(group_id=group_id, api_key=api_key, limit=limit)

    zotero_url += "&include={0}".format(include) if include else ""
    zotero_url += "&since={0}".format(since) if since else ""

    print("Retrieving most recent {limit} articles since version: {version}".format(limit=limit, version=since))

    response = urllib.request.urlopen(zotero_url)
    articles = json.loads(response.readall().decode('utf-8'))

    print("Retrieved {0} articles".format(len(articles)))

    return articles


def send_article_to_slack(webhook_url, article, channel=None, username=None, icon_emoji=None, verbose=True, mock=False):
    """Sends a JSON article to the given Slack Webhooks URL"""
    payload = {"text": format_article(article)}
    if channel:
        payload['channel'] = channel

    if username:
        payload['username'] = username

    if icon_emoji:
        payload['icon_emoji'] = icon_emoji

    response = None
    if not mock:
        response = requests.post(webhook_url, json=payload)
        if response.status_code != 200:
            print(
                'Request to slack returned an error %s, the response is:\n%s'
                % (response.status_code, response.text)
            )

    if verbose:
        version = int(article['version'])
        print("{0} - {1}".format(version, article['data']['title']))

    return response


def format_article(article):
    """Feel free to overwrite me with your preferred format"""
    data = article['data']
    meta = article['meta']

    title = data['title']

    submitter = meta.get('createdByUser', {}).get('username', '')

    itemType = data.get('itemType', '')
    if itemType == "thesis":
        journal = data.get('university', '')
    else:
        journal = data.get('publicationTitle', '')

    authors = meta.get('creatorSummary', '').rstrip(".")
    date = data.get('date', '')

    # Build citation
    citation = ""
    citation += (authors + ". ") if authors else ""
    citation += ("_" + journal + "_ ") if journal else ""
    citation += date if date else ""

    abstract = data.get('abstractNote', '')
    if abstract:
        # Extract first N words
        word_cnt = 100
        abstract_words = abstract.split(" ")
        abstract = " ".join(abstract_words[:word_cnt])
        if len(abstract_words) > word_cnt:
            abstract += " …"

    url = data.get('url', '').strip()
    doi = data.get('DOI', '')
    tags = [t['tag'] for t in data.get('tags', '')]

    link = ""
    if not doi and url:
        link = url
    elif doi:
        link = "https://doi.org/{0}".format(doi)

    template = ""
    template += "<{link}|*{title}*>\n" if link else "*{title}*\n"
    template += "*Citation:* {citation}\n" if citation else ""
    template += "*Tags:* {tags}\n" if tags else ""
    template += "*Added By:* {submitter}\n" if submitter else ""

    template += "\n*Abstract:*\n```{abstract}```" if abstract else ""

    return template.format(title=title, abstract=abstract, link=link, submitter=submitter,
                           citation=citation, tags=", ".join(tags))


def main(zotero_group, zotero_api_key, slack_webhook_url, since_version=0, channel=None, username=None, icon_emoji=None,
         limit=25, mock=False, verbose=True):
    timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

    articles = retrieve_articles(zotero_group, zotero_api_key, limit=limit if since_version else 1, since=since_version)

    max_version = max([since_version] + [article['version'] for article in articles])

    skipped = 0
    for article in reversed(articles):
        try:
            send_article_to_slack(slack_webhook_url, article, channel=channel, username=username, icon_emoji=icon_emoji,
                                  verbose=verbose, mock=mock)
        except Exception as inst:
            skipped += 1
            print("Problem Sending article {key}: {error}".format(key=article['key'], error=inst))

    print("Current Version: {0}".format(max_version))

    run_info = {"time": timestamp, "version": max_version, "articles_cnt": len(articles), "skipped": skipped}

    return run_info

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Retrieve most recent articles from a Zotero group using Zotero's "
                                                 "API v3 and send them to a Slack channel using Webhooks")

    parser.add_argument('--group', dest='group', type=int, required=False,
                        help='Zotero group ID of the library to monitor')

    parser.add_argument('--api', dest='api_key', type=str, required=False,
                        help='Zotero API key with access to the library')

    parser.add_argument('--webhook', dest='webhook', type=str, required=False,
                        help='Slack webhook URL to send articles')

    parser.add_argument('--since', dest='version', type=int, required=False, default=0,
                        help='Retrieve only articles created after this version')
    parser.add_argument('--limit', dest='limit', type=int, required=False, default=25,
                        help='Max articles to return when --since is supplied')
    parser.add_argument('--channel', dest='channel', type=str, required=False, default=None,
                        help='Override default Slack webhooks channel')
    parser.add_argument('--username', dest='username', type=str, required=False, default=None,
                        help='Override default Slack webhooks username')
    parser.add_argument('--icon', dest='icon_emoji', type=str, required=False, default=None,
                        help='Override default Slack webhooks icon')

    parser.add_argument('--artifact', dest='artifact', type=str, required=False, default=None,
                        help='Retrieve --since from & write run info to this file. OVERRIDES --since')

    parser.add_argument('--mock', dest='mock', action='store_true',
                        help='Mock run; will not write to Slack or filesystem')

    parser.add_argument('-v', dest='verbose', action='store_true',
                        help='More verbose logging')

    parser.add_argument('--test', dest='test', type=str, required=False, default=None,
                        help='Test output using JSON file, will not write to Slack or filesystem')

    args = parser.parse_args()

    since = args.version
    if args.artifact:
        try:
            with open(args.artifact) as data_file:
                data = json.load(data_file)
                since = data['version']
        except (FileNotFoundError, KeyError) as e:
            print("Error reading version info from artifact file, defaulting to {0}.".format(since))

    if args.test:
        # Monkey patching

        # Just in case
        args.mock = True

        try:
            with open(args.test) as data_file:
                articles = json.load(data_file)
        except (FileNotFoundError, KeyError) as e:
            print("Error reading test file.")
            articles = []

        def mocked_retrieve(*args, **kwargs):
            return articles

        retrieve_articles = mocked_retrieve

        def mocked_send(*args, **kwargs):
            print(format_article(args[1]))
            print("-------------------")

        send_article_to_slack = mocked_send

    run_info = main(args.group, args.api_key, args.webhook, since, args.channel, args.username, args.icon_emoji,
                    args.limit, args.mock, args.verbose)

    if not args.mock and not args.test and args.artifact:
        print("Writing run version to {artifact}".format(artifact=args.artifact))
        with open(args.artifact, 'w') as outfile:
            json.dump(run_info, outfile)

    if run_info['skipped']:
        # Articles were skipped, warn cron-like process by exiting with 2
        sys.exit(2)
