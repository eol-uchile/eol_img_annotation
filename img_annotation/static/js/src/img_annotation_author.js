/*
        .-"-.
       /|6 6|\
      {/(_0_)\}
       _/ ^ \_
      (/ /^\ \)-'
       ""' '""
*/


function ImgAnnotationAuthorXBlock(runtime, element, settings) {
  var $ = window.jQuery;
  var $element = $(element);
  var handlerUrl = runtime.handlerUrl(element, 'save_anno_xblock');
  var handlerRemoveAnnotation = runtime.handlerUrl(element, 'removestudentannotations');
  var handlerUpdateAnnotation = runtime.handlerUrl(element, 'updatestudentannotations_author');
  var anno;
  var selectorSquare = '<span class="a9s-toolbar-btn-inner"><svg viewBox="0 0 70 50"><g><rect x="12" y="10" width="46" height="30"></rect><g class="handles"><circle cx="12" cy="10" r="5"></circle><circle cx="58" cy="10" r="5"></circle><circle cx="12" cy="40" r="5"></circle><circle cx="58" cy="40" r="5"></circle></g></g></svg></span>';
  var selectorPolygon = '<svg viewBox="0 0 70 50"><g><path d="M 5,14 60,5 55,45 18,38 Z"></path><g class="handles"><circle cx="5" cy="14" r="5"></circle><circle cx="60" cy="5" r="5"></circle><circle cx="55" cy="45" r="5"></circle><circle cx="18" cy="38" r="5"></circle></g></g></svg>';
  if (Object.keys(settings.image_data).length > 0){
    $(function($) {
        var ColorSelectorWidget = function(args) {

          // 1. Find a current color setting in the annotation, if any
          var currentColorBody = args.annotation ? 
            args.annotation.bodies.find(function(b) {
              return b.purpose == 'highlighting';
            }) : null;
        
          // 2. Keep the value in a variable
          var currentColorValue = currentColorBody ? currentColorBody.value : null;
        
          // 3. Triggers callbacks on user action
          var addTag = function(evt) {
            if (currentColorBody) {
              args.onUpdateBody(currentColorBody, {
                type: 'TextualBody',
                purpose: 'highlighting',
                value: evt.target.dataset.tag
              });
            } else { 
              args.onAppendBody({
                type: 'TextualBody',
                purpose: 'highlighting',
                value: evt.target.dataset.tag
              });
            }
          }
        
          // 4. This part renders the UI elements
          var createButton = function(value) {
            var button = document.createElement('button');
        
            if (value == currentColorValue)
              button.className = 'selected';
        
            button.dataset.tag = value;
            button.style.backgroundColor = value;
            button.addEventListener('click', addTag); 
            return button;
          }
        
          var container = document.createElement('div');
          container.className = 'colorselector-widget';
          if(args.annotation.body[0] === undefined){
            args.annotation.body.push({"type": "TextualBody", "purpose": "highlighting", "value": "RED", "creator": {"id": settings.username, "name": settings.username}});
          }
          var button1 = createButton('RED');
          var button2 = createButton('GREEN');
          var button3 = createButton('BLUE');
        
          container.appendChild(button1);
          container.appendChild(button2);
          container.appendChild(button3);
        
          return container;
        }
        var ColorFormatter = function(annotation) {
          var highlightBody = annotation.bodies.find(function(b) {
            return b.purpose == 'highlighting';
          });
        
          if (highlightBody)
            return highlightBody.value;
        }
        osd = 'openseadragon-'+settings.location;
        var viewer = OpenSeadragon({
          id: osd,
          prefixUrl: settings.osd_resources,
          tileSources: settings.image_data,
          showNavigator:  true
        });
        anno = OpenSeadragon.Annotorious(viewer, {
          locale: 'auto',
          gigapixelMode: true,
          allowEmpty: true,
          formatter: ColorFormatter,
          widgets: [
            ColorSelectorWidget,
            {widget: 'COMMENT', editable: 'MINE_ONLY'},
          ]
        });
        //{widget: 'COMMENT', editable: 'MINE_ONLY', purposeSelector: true},
        toolbar = '#toolbar-'+settings.location;
        Annotorious.Toolbar(anno,  $(element).find(toolbar)[0]);
        anno.setAuthInfo({
          id: settings.username,
          displayName: settings.username
        });
        settings.annotation.forEach(annotation => {
          anno.addAnnotation(setAnnotation(annotation.id, annotation.body, annotation.target), true);
        });
        $(element).find(toolbar).find('.rect').find('.a9s-toolbar-btn-inner')[0].innerHTML = selectorSquare;
        $(element).find(toolbar).find('.polygon').find('.a9s-toolbar-btn-inner')[0].innerHTML = selectorPolygon;
    });
    anno.on('createAnnotation', function(annotation) {
      $(element).find('#img_annotation_wrong_label').hide();
      $.post(handlerUrl, JSON.stringify({'annotation':annotation})).done(function(response) {
        if(response.result != 'success'){
          $element.find('#img_annotation_wrong_label')[0].textContent = "Error en guardar, actualice la pagina e intente nuevamente.";
          $(element).find('#img_annotation_wrong_label').show();
        }
        let child = document.createElement("option");
        child.id = annotation.id.substring(1);
        child.value = annotation.id;
        child.innerText = 'Anotacion ' + $(element).find('select[name=annotations_xblock]')[0].children.length;
        $(element).find('select[name=annotations_xblock]')[0].appendChild(child);
      });
    });
    anno.on('deleteAnnotation', function(annotation) {
      $(element).find('#img_annotation_wrong_label').hide();
      $.post(handlerRemoveAnnotation, JSON.stringify({'id':annotation.id})).done(function(response) {
        if(response.result != 'success'){
          $element.find('#img_annotation_wrong_label')[0].textContent = "Error en borrar, actualice la pagina e intente nuevamente.";
          $(element).find('#img_annotation_wrong_label').show();
        }
        var select = $(element).find('select[name=annotations_xblock]');
        select[0].removeChild(select.find(annotation.id)[0]);
      });
    });
    anno.on('updateAnnotation', function(annotation, previous) {
      $(element).find('#img_annotation_wrong_label').hide();
      $.post(handlerUpdateAnnotation, JSON.stringify({'annotation':annotation})).done(function(response) {
        if(response.result != 'success'){
          $element.find('#img_annotation_wrong_label')[0].textContent = "Error en editar, actualice la pagina e intente nuevamente.";
          $(element).find('#img_annotation_wrong_label').show();
        }
      });
    });
    $(element).find('select[name=annotations_xblock]')[0].addEventListener('change', function() {
      if(this.value != "0"){
        anno.selectAnnotation(this.value);
        anno.panTo(this.value, true);
      }
    });
    function setAnnotation(id, body, target) {
      type = "FragmentSelector";
      if (target.includes('svg')){
        type = "SvgSelector";
      }
      return {
        "type": "Annotation",
        "body": body,
        "target": {
          "selector": {
            "type": type,
            "conformsTo": "http://www.w3.org/TR/media-frags/",
            "value": target
          }
        },
        "@context": "http://www.w3.org/ns/anno.jsonld",
        "id": id
      }
    }
  }
}