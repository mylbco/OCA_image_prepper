import json

from flask import Flask, request, render_template
import requests
import os.path

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
    Selected repositories are being downloaded to "/gh_oca_addons".
    Run docker-compose once all selected repos have been downloaded.
    """
    if request.method == 'GET':
        repos_json = './repos.json'
        if os.path.isfile(repos_json):
            with open(repos_json, 'r') as rf:
                repos = json.loads(rf.read())

        else:
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

            with open(repos_json, 'w') as rf:
                rf.write(json.dumps(repos, indent=4))

        return render_template("base.html", repos=repos)

    if request.method == 'POST':
        repos = request.form

        import subprocess

        for repo in repos.values():
            proc = subprocess.run(
                f"rm -rf tmp && git  --depth 1 {repo} tmp && cp -rf tmp/* gh_oca_addons && rm -rf tmp",
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
                )

            if proc.returncode != 0:
                return proc.stderr

        return "Ready!"
