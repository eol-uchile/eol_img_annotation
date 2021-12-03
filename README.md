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

## Notes

Add the following code here _../themes/your_theme/cms/templates/container.html_

    <% have_img_annotation = False %>
    %for child in xblock.children:
        %if child.block_type == 'img_annotation':
            <% have_img_annotation = True %>
        % endif
    % endfor
    % if have_img_annotation:
        <script id='openseadragon-scripts' type="text/javascript" src="${static.url('img_annotation/openseadragon.2.4.2.min.js')}"></script>
        <script type="text/javascript" src="${static.url('img_annotation/openseadragon-annotorious.min.js')}"></script>
        <script type="text/javascript" src="${static.url('img_annotation/annotorious-toolbar.min.js')}"></script>
    % endif
