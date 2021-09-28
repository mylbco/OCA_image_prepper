# OCA_image_prepper
A small Flask application that let's you pick all available extra addons from the OCA that you need for your Odoo (test) installation.

### Setup
```bash
python -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
flask run
```
Open your browser and go to the address displayed in your terminal.
Select the OCA modules that you need.
Press the `Submit` button and wait until you see the "Ready!"

Once the flask app has done it's work, it's time to spin up our docker container:
```bash
docker-compose up
```

### What is this 'repos.json' file?
The first time that our flask app tries to locate all the OCA modules on Github, it doesn't have this information locally.
So we will fetch the most recent data via the Github API. The traffic on the API is limited for anonymous users, hence
the local "cache" file.

## FAQ

### How do I update the information in my local "cache" file?
Simply by deleting the file and rerunning the flask app.