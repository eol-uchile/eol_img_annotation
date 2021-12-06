/*
        .-"-.
       /|6 6|\
      {/(_0_)\}
       _/ ^ \_
      (/ /^\ \)-'
       ""' '""
*/

//https://studio.luis.msalinas.cl/static/xblock/resources/img_annotation/static/images/dzi/mydz.dzi
function ImgAnnotationXBlock(runtime, element, settings) {
    var $ = window.jQuery;
    var $element = $(element);
    var handlerSaveAnnotation = runtime.handlerUrl(element, 'savestudentannotations');
    var handlerRemoveAnnotation = runtime.handlerUrl(element, 'removestudentannotations');
    var handlerUpdateAnnotation = runtime.handlerUrl(element, 'updatestudentannotations');
    var handlerUpdateAnnotationStaff = runtime.handlerUrl(element, 'updatestudentannotationsstaff');
    var handlerUrlSaveStudentAnswers = runtime.handlerUrl(element, 'save_data_student');
    var get_student_data = runtime.handlerUrl(element, 'get_student_data');
    var get_student_annotation = runtime.handlerUrl(element, 'get_student_annotation');
    var onAnnotation = '';
    var anno;
    var removeEditDropdown;
    var selectorSquare = '<span class="a9s-toolbar-btn-inner"><svg viewBox="0 0 70 50"><g><rect x="12" y="10" width="46" height="30"></rect><g class="handles"><circle cx="12" cy="10" r="5"></circle><circle cx="58" cy="10" r="5"></circle><circle cx="12" cy="40" r="5"></circle><circle cx="58" cy="40" r="5"></circle></g></g></svg></span>';
    var selectorPolygon = '<svg viewBox="0 0 70 50"><g><path d="M 5,14 60,5 55,45 18,38 Z"></path><g class="handles"><circle cx="5" cy="14" r="5"></circle><circle cx="60" cy="5" r="5"></circle><circle cx="55" cy="45" r="5"></circle><circle cx="18" cy="38" r="5"></circle></g></g></svg>';  
    removeEditDropdown = function() {
      return $(".r6o-lastmodified-by:contains(" + settings.username + ")").parent().parent().find('.r6o-icon').hide();
    };
    if (settings.image_url != ""){
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
              button.className = 'remove-all-styles';
              if (value == currentColorValue)
                button.className = button.className + ' selected';
          
              button.dataset.tag = value;
              button.style.backgroundColor = value;
              button.addEventListener('click', addTag); 
              return button;
            }
          
            var container = document.createElement('div');
            container.className = 'colorselector-widget';
            if(args.annotation.body[0] === undefined){
              var creator = settings.username
              args.annotation.body.push({"type": "TextualBody", "purpose": "highlighting", "value": "RED", "creator": {"id": creator, "name": creator}});
            }
            else{
              var creator = args.annotation.body[0].creator.name;
            }
            if(! settings.list_annotation_staff.includes(args.annotation.id) && creator == settings.username && settings.score == ''){
              var button1 = createButton('RED');
              var button2 = createButton('GREEN');
              var button3 = createButton('BLUE');
              container.appendChild(button1);
              container.appendChild(button2);
              container.appendChild(button3);
            }
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
              tileSources: settings.image_url,
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
          if (settings.is_course_staff){
            anno.setAuthInfo({
              id: settings.username+'.',
              displayName: settings.username+'.'
            });
            $(element).find('input[name=puntaje]')[0].disabled = true;
            $(element).find('textarea[name=comentario]')[0].disabled = true;
            $(element).find('input[name=img-annotation-save]')[0].disabled = true;
            $(element).find('input[name=img-annotation-save]').hide();
            anno.readOnly = true;
            settings.annotation_staff.forEach(annotation => {
              anno.addAnnotation(setAnnotation(annotation.id, annotation.body, annotation.target));
            });
            anno.on('updateAnnotation', function(annotation, previous) {
              var student_id = $(element).find('input[name=img-annotation-save]')[0].getAttribute('aria-controls');
              $(element).find('#img_annotation_wrong_main').hide();
              $.post(handlerUpdateAnnotationStaff, JSON.stringify({'annotation':annotation, 'student_id': student_id})).done(function(response) {
                if(response.result != 'success'){
                  $element.find('#img_annotation_wrong_main')[0].textContent = "Error en editar, actualice la página e intente nuevamente.";
                  $(element).find('#img_annotation_wrong_main').show();
                }
              });
            });
            anno.on('cancelSelected', function(selection) {
              if(selection.id == onAnnotation){
                anno.readOnly = true;
              }
            });
            anno.on('selectAnnotation', function(annotation) {
              if(settings.list_annotation_staff.includes(annotation.id)){
                $('.r6o-icon.r6o-arrow-down').show();
                return setTimeout(removeEditDropdown, 40);
              }
            });
            anno.on('clickAnnotation', function(annotation) {
              onAnnotation = annotation.id;
              if(settings.list_annotation_staff.includes(annotation.id)){
                anno.readOnly = true;
              }
              else{
                anno.readOnly = false;
              }
            });
          }
          else{
            anno.setAuthInfo({
              id: settings.username,
              displayName: settings.username
            });
            settings.annotation_staff.forEach(annotation => {
              anno.addAnnotation(setAnnotation(annotation.id, annotation.body, annotation.target));
            });
            settings.annotation.forEach(annotation => {
              anno.addAnnotation(setAnnotation(annotation.id, annotation.body, annotation.target));
            });
            if (settings.score == ''){
              toolbar = '#toolbar-'+settings.location;
              Annotorious.Toolbar(anno, $(element).find(toolbar)[0]);
              $(element).find(toolbar).find('.rect').find('.a9s-toolbar-btn-inner')[0].innerHTML = selectorSquare;
              $(element).find(toolbar).find('.polygon').find('.a9s-toolbar-btn-inner')[0].innerHTML = selectorPolygon;
              anno.on('createAnnotation', function(annotation) {
                $(element).find('#img_annotation_wrong_main').hide();
                $.post(handlerSaveAnnotation, JSON.stringify({'annotation':annotation})).done(function(response) {
                  if(response.result != 'success'){
                    $element.find('#img_annotation_wrong_main')[0].textContent = "Error en guardar, actualice la página e intente nuevamente.";
                    $(element).find('#img_annotation_wrong_main').show();
                  }
                  let child = document.createElement("option");
                  child.id = annotation.id.substring(1);
                  child.value = annotation.id;
                  child.innerText = 'Anotación ' + $(element).find('select[name=annotations_student]')[0].children.length;
                  $(element).find('select[name=annotations_student]')[0].appendChild(child);
                });
              });
              anno.on('deleteAnnotation', function(annotation) {
                $(element).find('#img_annotation_wrong_main').hide();
                $.post(handlerRemoveAnnotation, JSON.stringify({'id':annotation.id})).done(function(response) {
                  if(response.result != 'success'){
                    $element.find('#img_annotation_wrong_main')[0].textContent = "Error en borrar, actualice la página e intente nuevamente.";
                    $(element).find('#img_annotation_wrong_main').show();
                  }
                  var select = $(element).find('select[name=annotations_student]');
                  select[0].removeChild(select.find(annotation.id)[0]);
                });
              });
              anno.on('updateAnnotation', function(annotation, previous) {
                $(element).find('#img_annotation_wrong_main').hide();
                $.post(handlerUpdateAnnotation, JSON.stringify({'annotation':annotation})).done(function(response) {
                  if(response.result != 'success'){
                    $element.find('#img_annotation_wrong_main')[0].textContent = "Error en editar, actualice la página e intente nuevamente.";
                    $(element).find('#img_annotation_wrong_main').show();
                  }
                });
              });
              anno.on('cancelSelected', function(selection) {
                if(selection.id == onAnnotation){
                  anno.readOnly = false;
                }
              });
              anno.on('selectAnnotation', function(annotation) {
                if(settings.list_annotation_staff.includes(annotation.id)){
                  $('.r6o-icon.r6o-arrow-down').show();
                  return setTimeout(removeEditDropdown, 40);
                }
              });
              anno.on('clickAnnotation', function(annotation) {
                onAnnotation = annotation.id;
                if(settings.list_annotation_staff.includes(annotation.id)){
                  anno.readOnly = true;
                }
                else{
                  anno.readOnly = false;
                }
              });
            }
            else{
              anno.readOnly = true;
              anno.on('selectAnnotation', function(annotation) {
                $('.r6o-icon.r6o-arrow-down').show();
                return setTimeout(removeEditDropdown, 40);
              });
              ;
            }
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
      $(element).find('select[name=annotations_student]')[0].addEventListener('change', function() {
        $('.r6o-icon.r6o-arrow-down').show();
        setTimeout(removeEditDropdown, 40);
        onAnnotation = this.value;
        anno.readOnly = false;
        $(element).find('select[name=annotations_author]')[0].value = "0";
        if(this.value != "0"){
          anno.selectAnnotation(this.value);
          anno.panTo(this.value, true);
        }
      });
      $(element).find('select[name=annotations_author]')[0].addEventListener('change', function() {
        $('.r6o-icon.r6o-arrow-down').show();
        setTimeout(removeEditDropdown, 40);
        onAnnotation = this.value;
        anno.readOnly = true;
        $(element).find('select[name=annotations_student]')[0].value = "0";
        if(this.value != "0"){
          anno.selectAnnotation(this.value);
          anno.panTo(this.value, true);
        }
      });
      function findPos(obj) {
        var curtop = 0;
        if (obj.offsetParent) {
            do {
                curtop += obj.offsetTop;
            } while (obj = obj.offsetParent);
        return [curtop];
        }
      }
      function removeAnnotations(anno){
        var annotations =anno.getAnnotations();
        annotations.forEach(annotation => {
          anno.removeAnnotation(annotation.id)
        });
      }
      function create_modal_content(lista_alumnos){
        modal_content = $(element).find('#tabla-alumnos');
        var html_content = "";
        for (var i = 0; i < lista_alumnos.length; i++) {
            html_content = html_content + create_accordion_user(lista_alumnos[i]);
        }
        modal_content.html(html_content);
      }
      function create_accordion_user(datos){
        var tr = '<tr>';
        if (datos['score'] != ''){
          tr = '<tr class="class_scored_user">';
        }
        var id_student = '<td hidden>'+datos['id']+'</td>';
        var username = '<td>'+datos['username']+'</td>';
        var score = '<td>'+datos['score']+'</td>';
        var boton = '<td><input type="button" aria-controls="'+datos['id'] +'" aria-username="'+datos['username'] +'" value="Ver Annotaciones"/><div id="ui-loading-img-annotation-load-button" class="ui-loading is-hidden" style="box-shadow: none;background: none;padding: 0;">'+
        '<p><span class="spin"><span class="icon fa fa-refresh" aria-hidden="true"></span>'+
        '</span></p></div></td>';
        return tr+id_student+username+score+boton+'</tr>'
      }
      function changeSelectAnnotation(annotations){
        var select_content = $(element).find('select[name=annotations_student]');
        var html_content = '<option value="0" selected>Seleccione una Anotación</option>';
        for (var i = 0; i < annotations.length; i++) {
            html_content = html_content + create_select_student(annotations[i], i+1);
        }
        select_content.html(html_content);
      }
      function create_select_student(datos, i){
        //<option id="{{ x|slice:'1:' }}" value="{{ x }}">Anotación {{ forloop.counter }}</option>
        var option = '<option id +"';
        var id_anno = datos['id'].substring(1);
        var value = datos['id'];
        return option+id_anno+'" value="'+value+'">Anotación '+i+'</option>'
      }
      $(element).find('input[name=checkbox_users]').live('change', function(e) {
        if (e.target.checked) {
            $(element).find('.class_scored_user').hide()
        }
        else {
            $(element).find('.class_scored_user').show()
        }
      });
      $(element).find('input[name=checkbox_annotation]').live('change', function(e) {
        if (e.target.checked) {
          settings.annotation_staff.forEach(annotation => {
            anno.addAnnotation(setAnnotation(annotation.id, annotation.body, annotation.target));
          });
          $(element).find('#annotations_author_class').show();
        }
        else {
          $(element).find('#annotations_author_class').hide();
          settings.list_annotation_staff.forEach(id => {
            anno.removeAnnotation(id)
          });
        }
      });
      $(element).find('tr input[type=button]').live('click', function(e) {
        $(element).find('input[name=checkbox_annotation]')[0].checked = false;
        $(element).find('#annotations_student_class').hide();
        $(element).find('#annotations_author_class').hide();
        $(element).find('#header_username').hide();
        $(element).find('#calificacion_student').hide();
        $(element).find('#img_annotation_footer').hide();
        $(element).find('#img_annotation_wrong_footer').hide();
        $(this).parent().find("#ui-loading-img-annotation-load-button").show();
        $(element).find('#img_annotation_wrong_label').hide();
        var id_student = e.target.getAttribute('aria-controls');
        var username = e.target.getAttribute('aria-username');
        e.target.disabled = true;
      
        if(id_student != ""){
          $.post(get_student_annotation, JSON.stringify({"id": id_student})).done(function(response) {
            removeAnnotations(anno);
            changeSelectAnnotation(response.annotation);
            $element.find('#student_username_2')[0].textContent = username;
            $element.find('#student_username')[0].textContent = username;
            $(element).find('#annotations_student_class').show();
            $(element).find('#calificacion_student').show();
            $(element).find('#header_username').show();
            response.annotation.forEach(annotation => {
              anno.addAnnotation(setAnnotation(annotation.id, annotation.body, annotation.target));
            });
            $(element).find('input[name=puntaje]')[0].disabled = false;
            $(element).find('textarea[name=comentario]')[0].disabled = false;
            $(element).find('input[name=img-annotation-save]')[0].disabled = false;
            $(element).find('input[name=img-annotation-save]')[0].setAttribute("aria-controls", id_student);
            $(element).find('input[name=img-annotation-random]')[0].setAttribute("aria-controls", id_student);
            $(element).find('input[name=img-annotation-save]').show();
            $(element).find('input[name=puntaje]')[0].value = response.score;
            $(element).find('textarea[name=comentario]')[0].value = response.comment;
            var modal = '#grade-1-img-annotation-'+ settings.location;
            $(modal).hide();
          }).fail(function() {
              $element.find('#img_annotation_wrong_label')[0].textContent = "Actualice la página e intente nuevamente.";
              $(element).find('#img_annotation_wrong_label')[0].style.display = 'block';
              $(this).parent().find("#ui-loading-img-annotation-load-button").hide();
          });
        }
        else{
            $element.find('#img_annotation_wrong_label')[0].textContent = "Actualice la página e intente nuevamente.";
            $(element).find('#img_annotation_wrong_label')[0].style.display = 'block';
            $(this).parent().find("#ui-loading-img-annotation-load-button").hide();
        }
      });
      $(element).find('a[name=img-annotation-button]').live('click', function(e) {
        e.preventDefault();
        e.currentTarget.disabled = true;
        $element.find('#img_annotation_wrong_label')[0].textContent = "";
        $element.find('#img_annotation_wrong_label')[0].style.display = "none";
        $(element).find('#ui-loading-img-annotation-load').show()
        var id_modal = $(this)[0].getAttribute('aria-controls')
        var forum_modal =  document.getElementById(id_modal)
        $.post(get_student_data, JSON.stringify({})).done(function(response) {
          //{'result': 'success', 'lista_alumnos': lista_alumnos}
          if (response.result == 'success' ){
              titulo = $(element).find('#img-annotation-body')
              titulo.html('Puntaje máximo: ' + settings.puntajemax);
              create_modal_content(response.lista_alumnos);
          }
          else {
              titulo = $(element).find('#img-annotation-body');
              titulo.html('Usuario no tiene permisos para obtener los datos.');
              
          }
          $(element).find('#ui-loading-img-annotation-load').hide();
          forum_modal.style.display = "block";
          window.scroll(0,findPos(document.getElementById(id_modal)) - 450);
          e.currentTarget.disabled = false;
        }).fail(function() {
            titulo = $(element).find('#img-annotation-body')
            titulo.html('Se ha producido un error en obtener los datos.');
            $(element).find('#ui-loading-img-annotation-load').hide();
            forum_modal.style.display = "block";
            window.scroll(0,findPos(document.getElementById(id_modal)) - 450);
            e.currentTarget.disabled = false;
        });
      });
      $(element).find('input[name=img-annotation-save]').live('click', function(e) {
        e.target.disabled = true;
        $(element).find('#ui-loading-img-annotation-footer').show();
        $(element).find('#img_annotation_footer').hide();
        $(element).find('#img_annotation_wrong_footer').hide();
        var student_id = e.target.getAttribute('aria-controls');
        var puntaje = $(element).find('input[name=puntaje]')[0].value;
        var comentario = $(element).find('textarea[name=comentario]')[0].value;
        var pmax = settings.puntajemax;
        if(puntaje != "" && !(puntaje.includes(".")) && parseInt(puntaje, 10) <= parseInt(pmax, 10) && parseInt(puntaje, 10) >= 0){
            $.post(handlerUrlSaveStudentAnswers, JSON.stringify({"student_id": student_id, "puntaje": puntaje, "comentario": comentario})).done(function(response) {
              if (response.result == 'success' ){
                $element.find('#img_annotation_footer')[0].textContent = 'Guardado Correctamente.';
                $(element).find('#img_annotation_footer').show();
                if(!response.calificado){
                  $element.find("#calificado")[0].textContent = parseInt($element.find("#calificado")[0].textContent) + 1;
                }
                e.target.disabled = false;
                var index = settings.list_student.indexOf(Number(student_id));
                if (index > -1) {
                  settings.list_student.splice(index, 1);
                }
              }
              else {
                $element.find('#img_annotation_wrong_footer')[0].textContent = 'Error - Actualice la página e intente nuevamente.';
                $(element).find('#img_annotation_wrong_footer').show();
              }
              $(element).find('#ui-loading-img-annotation-footer').hide();
            }).fail(function() {
              $element.find('#img_annotation_wrong_footer')[0].textContent = 'Error - Actualice la página e intente nuevamente.';
              $(element).find('#img_annotation_wrong_footer').show();
              $(element).find('#ui-loading-img-annotation-footer').hide();
            });
        }
        else{
            $element.find('#img_annotation_wrong_footer')[0].textContent = "Puntaje incorrecto, el puntaje debe ser un número entero entre 0 y " + pmax + '.';
            $element.find('#img_annotation_footer')[0].textContent = "";
            $(element).find('#img_annotation_footer').hide();
            $(element).find('#img_annotation_wrong_footer').show();
            $(element).find('#ui-loading-img-annotation-footer').hide();
            e.target.disabled = false;
        }
      });
      function getRndInteger(min, max) {
        return Math.floor(Math.random() * (max - min) ) + min;
      }
      $(element).find('input[name=img-annotation-random]').live('click', function(e) {
        console.log(settings.list_student);
        e.target.disabled = true;
        $(element).find('input[name=checkbox_annotation]')[0].checked = false;
        $(element).find('input[name=puntaje]')[0].disabled = true;
        $(element).find('textarea[name=comentario]')[0].disabled = true;
        $(element).find('#annotations_student_class').hide();
        $(element).find('#annotations_author_class').hide();
        $(element).find('#header_username').hide();
        $(element).find('#calificacion_student').hide();
        $(element).find('#ui-loading-img-annotation-random').show();
        $(element).find('#img_annotation_footer').hide();//label
        $(element).find('#img_annotation_wrong_footer').hide();
        $(element).find('input[name=img-annotation-save]').hide();
        let aux_list_student = settings.list_student.slice();
        var current_student = e.target.getAttribute('aria-controls');
        var aux_index = aux_list_student.indexOf(Number(current_student));
        var id_student = "";
        if (aux_index > -1) {
          aux_list_student.splice(aux_index, 1);
        }
        if(aux_list_student.length > 0){
          var index_student = getRndInteger(0, aux_list_student.length);
          id_student = aux_list_student[index_student];
        }
        delete aux_list_student;
        if(id_student != ""){
          $.post(get_student_annotation, JSON.stringify({"id": id_student})).done(function(response) {
            removeAnnotations(anno);
            changeSelectAnnotation(response.annotation);
            $element.find('#student_username_2')[0].textContent = response.username;
            $element.find('#student_username')[0].textContent = response.username;
            $(element).find('#annotations_student_class').show();
            $(element).find('#calificacion_student').show();
            $(element).find('#header_username').show();
            response.annotation.forEach(annotation => {
              anno.addAnnotation(setAnnotation(annotation.id, annotation.body, annotation.target));
            });
            e.target.disabled = false;
            $(element).find('input[name=puntaje]')[0].disabled = false;
            $(element).find('textarea[name=comentario]')[0].disabled = false;
            $(element).find('input[name=img-annotation-save]')[0].disabled = false;
            $(element).find('input[name=img-annotation-save]')[0].setAttribute("aria-controls", id_student);
            $(element).find('input[name=img-annotation-random]')[0].setAttribute("aria-controls", id_student);
            $(element).find('input[name=img-annotation-save]').show();
            $(element).find('input[name=puntaje]')[0].value = response.score;
            $(element).find('textarea[name=comentario]')[0].value = response.comment;
            $(element).find('#ui-loading-img-annotation-random').hide();
          }).fail(function() {
              $element.find('#img_annotation_wrong_footer')[0].textContent = "Actualice la página e intente nuevamente.";
              $(element).find('#img_annotation_wrong_footer').show();
              $(element).find('#ui-loading-img-annotation-random').hide();
          });
        }
        else{
            $element.find('#img_annotation_footer')[0].textContent = "Todos los estudiantes han sido evaluados.";
            $(element).find('#img_annotation_footer').show();
            $(element).find('#ui-loading-img-annotation-random').hide();
        }
      });
    }
}
