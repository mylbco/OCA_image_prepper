#!/usr/bin/env python
"""
OCA image prepper

A small Flask application that let's you pick all available extra addons from
the OCA that you need for your Odoo test installation.
"""
import json
import shutil
import re
import requests
import os.path
import yaml
from io import BytesIO
from flask import Flask, request, render_template
from zipfile import ZipFile

app = Flask(__name__)


def parse_next_url(link):
    """
    This function handles the pagination of the Github API

    input that needs parsing:
    '<https://api.github.com/organizations/7600578/repos?page=2>; rel="next", \
    <https://api.github.com/organizations/7600578/repos?page=7>; rel="last"'

    or:
    <https://api.github.com/organizations/7600578/repos?page=1>; rel="prev", \
    <https://api.github.com/organizations/7600578/repos?page=3>; rel="next", \
    <https://api.github.com/organizations/7600578/repos?page=7>; rel="last", \
    <https://api.github.com/organizations/7600578/repos?page=1>; rel="first"

    :param link: headers['link'] retrieved from Github
    :return: next url
    """
    urls = link.split(", ")
    for u in urls:
        if "next" in u:
            next_url = u[1:].split(">")[0]
            return next_url

    next_url = None
    return next_url


@app.route('/', methods=['GET', 'POST'])
def list_oca_repos():
    """
    GET:
    Draw a table with 2 columns (checkbox, repository name)
    and a Submit button.

    POST:
    Selected repositories are being downloaded to "./tmp" and then copied over
    to "./gh_oca_addons". A "Ready!" message will appear once all repos
    have been copied over.
    """
    if request.method == 'GET':
        # check if we have a local 'cache'file
        repos_json = './repos.json'
        if os.path.isfile(repos_json):
            with open(repos_json, 'r') as rf:
                repos = json.loads(rf.read())

        else:
            # If we don't have a local 'cache'file, we need to refresh the data
            url = "https://api.github.com/orgs/OCA/repos?page=1"
            repos = list()

            while url:
                resp = requests.get(url)

                if resp.status_code == 200:
                    result = resp.json()
                    repos.extend(result)
                    links = resp.headers['link']
                    url = parse_next_url(links)

                # free API limit reached
                elif resp.status_code == 403:
                    return resp.content

            # Create a local "cache"file
            with open(repos_json, 'w') as rf:
                rf.write(json.dumps(repos, indent=4))

        # Get the Odoo version number from the branches
        url = "https://api.github.com/repos/odoo/odoo/branches"
        versions = list()

        resp = requests.get(url)

        if resp.status_code == 200:
            json_resp = resp.json()

            version_rex = "^[0-9]{2}\.[0-9]{1}$"    # match: '00.0'
            for jr in json_resp:
                if re.match(version_rex, jr['name']):
                    versions.append(jr['name'])

        versions.sort(reverse=True)

        # sort the list of repos alphabetically by name
        repos.sort(key=lambda repo: repo['name'])
        return render_template("base.html", repos=repos, versions=versions)

    if request.method == 'POST':
        repos = request.form
        dropdown = request.form['dropdown']

        # Download all repos in zip format and extract them in a
        # temporary directory
        for repo in repos:
            if repo != "dropdown":
                url = f"https://github.com/OCA/{repo}/archive/refs/heads/14.0.zip"
                with requests.get(url) as resp:
                    with ZipFile(BytesIO(resp.content)) as zipf:
                        zipf.extractall("./tmp/")

                # list of files/patterns that we want to ignore
                ignore = shutil.ignore_patterns(
                    ".*",
                    "LICENSE",
                    "*.md",
                    "*.txt"
                )
                # Copy everything over to "./gh_oca_addons/"
                shutil.copytree(
                    f"./tmp/{repo}-14.0",
                    "./gh_oca_addons",
                    ignore=ignore,
                    dirs_exist_ok=True
                )

        # clean up
        shutil.rmtree('tmp', ignore_errors=True)

        # generate our docker-compose.yml
        with open("dc-base.yml", "r") as y:
            file = yaml.load(y, yaml.SafeLoader)

        file['services']['web']['image'] = \
            f"{file['services']['web']['image'].split(':')[0]}:{dropdown}"

        # file = dict(sorted(file.items(), key=lambda x: x[0]))
        with open("docker-compose.yml", "w") as dc:
            yaml.dump(file, dc, sort_keys=False)

        return "Ready!"
