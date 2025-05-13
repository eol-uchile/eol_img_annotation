# Imagen Annotation XBlock

![Coverage Status](/coverage-badge.svg)

![https://github.com/eol-uchile/eol_img_annotation/actions](https://github.com/eol-uchile/eol_img_annotation/workflows/Python%20application/badge.svg)

# Install

    docker-compose exec cms pip install -e /openedx/requirements/eol_img_annotation
    docker-compose exec lms pip install -e /openedx/requirements/eol_img_annotation
    docker-compose exec lms python manage.py lms --settings=prod.production makemigrations
    docker-compose exec lms python manage.py lms --settings=prod.production migrate

## TESTS
**Prepare tests:**

- Install **act** following the instructions in [https://nektosact.com/installation/index.html](https://nektosact.com/installation/index.html)

**Run tests:**
- In a terminal at the root of the project
    ```
    act -W .github/workflows/pythonapp.yml
    ```

## Notes

Add the following code here _../themes/your_theme/cms/templates/container.html_

    <% have_img_annotation = False %>
    %for child in xblock.children:
        %if child.block_type == 'img_annotation':
            <% have_img_annotation = True %>
        % endif
    % endfor
    % if have_img_annotation:
        <script id='openseadragon-scripts' type="text/javascript" src="${static.url('js/src/openseadragon.5.0.1.min.js')}"></script>
        <script type="text/javascript" src="${static.url('js/src/openseadragon-annotorious.min.js')}"></script>
        <script type="text/javascript" src="${static.url('js/src/annotorious-toolbar.min.js')}"></script>
    % endif
