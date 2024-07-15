# Missing Persons & Unidentified Dead Bodies

An application for the automatic matching of missing persons with unidentified dead bodies

[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
[![Black code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)


## The Problem

One of the oldest problems of the policing system in India is the matching of unidentified dead bodies with missing person reports. This application attempts to solve that problem with the use of information technology. The main obstacles in the process of identification are identified and addressed. The application developed as a result of this analysis was successfully tested against live data of missing person reports and unidentified dead bodies in the state of West Bengal.

Here is a detailed introduction to the app:

[Detailed Introduction](https://drive.google.com/file/d/1byOUWPfPF7nHIESkGlOUdJVXdAWevD_h/view?usp=share_link)

## Deployment

The following details how to deploy this application.

    $ git clone https://github.com/sanjaysingh13/missing_and_found_wbsdc.git
    $ cd ~/missing_and_found_wbsdc
    $ python -m venv missing_found
    $ source missing_found/bin/activate
    $ pip install -r requirements/local.txt
    $ pip install -r requirements/production.txt
    $ gunicorn -c config/gunicorn/prod.py
    In a separate terminal window..
    $ celery -A config.celery_app worker -l info
    In another one..
    $ celery -A config.celery_app beat -l info
Use nginx to serve the web-page
You would need to set a number of environment variables, such as keys for AWS S3, Sendgrid, DATABASE_URL (Postgres), CELERY_BROKER_URL, MAP_BOX_ACCESS_TOKEN, SENTRY_DSN, RECAPTCHA_PUBLIC_KEY, RECAPTCHA_PRIVATE_KEY, etc.. You can find a full list in [base.py](./config/settings/base.py), [local.py](./config/settings/local.py) and [production.py](./config/settings/production.py)

Please contact the author if you are not sure how to register for and get these credentials.

## Settings

Moved to [settings](http://cookiecutter-django.readthedocs.io/en/latest/settings.html).

## Basic Commands

### Setting Up Your Users

-   To create a **normal user account**, just go to Sign Up and fill out the form. Once you submit it, you'll see a "Verify Your E-mail Address" page. Go to your console to see a simulated email verification message. Copy the link into your browser. Now the user's email should be verified and ready to go.

-   To create a **superuser account**, use this command:

        $ python manage.py createsuperuser

For convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox (or similar), so that you can see how the site behaves for both kinds of users.

### Type checks

Running type checks with mypy:

    $ mypy missing_persons_match_unidentified_dead_bodies

### Test coverage

To run the tests, check your test coverage, and generate an HTML coverage report:

    $ coverage run -m pytest
    $ coverage html
    $ open htmlcov/index.html

#### Running tests with pytest

    $ pytest

### Live reloading and Sass CSS compilation

Moved to [Live reloading and SASS compilation](https://cookiecutter-django.readthedocs.io/en/latest/developing-locally.html#sass-compilation-live-reloading).

### Celery

This app comes with Celery.

To run a celery worker:

``` bash
cd missing_persons_match_unidentified_dead_bodies
celery -A config.celery_app worker -l info
```

Please note: For Celery's import magic to work, it is important *where* the celery commands are run. If you are in the same folder with *manage.py*, you should be right.
