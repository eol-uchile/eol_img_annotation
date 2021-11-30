# Imagen Annotation XBlock

![https://github.com/eol-uchile/eol_img_annotation/actions](https://github.com/eol-uchile/eol_img_annotation/workflows/Python%20application/badge.svg)

# Install

    docker-compose exec cms pip install -e /openedx/requirements/eol_img_annotation
    docker-compose exec lms pip install -e /openedx/requirements/eol_img_annotation
    docker-compose exec lms python manage.py lms --settings=prod.production makemigrations
    docker-compose exec lms python manage.py lms --settings=prod.production migrate

## TESTS
**Prepare tests:**

    > cd .github/
    > docker-compose run --rm lms /openedx/requirements/eol_img_annotation/.github/test.sh

## Fix

- OpenSeaDragon js in cms can not load

