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
  var handlerSaveOverlay = runtime.handlerUrl(element, 'save_overlay_xblock');
  var handlerDeleteOverlay = runtime.handlerUrl(element, 'delete_overlay_xblock');
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

        var createRectangleButton = document.getElementById("overlay-draw-button-" + settings.location);
        var createArrowButton = document.getElementById("overlay-draw-button-arrow-" + settings.location);

          // Function to toggle pressed state and disable viewer zoom and movement while adding overlays.
          function toggleButtonState(button) {
            // If the button is already pressed, unpress it and enable image movement.
            if (button.classList.contains('pressed')) {
              button.classList.remove('pressed');
              // Adds a small delay to avoid zooming in after adding an arrow.
              setTimeout(() => {
                viewer.panHorizontal = true;
                viewer.panVertical = true;
                viewer.zoomPerClick = 2;
                viewer.zoomPerScroll = 1.2;
              }, 200);
            } else {
              // Otherwise mark it as pressed and disable image movement.
              button.classList.add('pressed');
              viewer.panHorizontal = false;
              viewer.panVertical = false;
              viewer.zoomPerClick = 1;
              viewer.zoomPerScroll = 1;
            }
          };

          createRectangleButton.addEventListener('click', () => {
            // Unpress other button if it's pressed.
            if (createArrowButton.classList.contains('pressed')) {
              createArrowButton.classList.remove('pressed');
            }
            toggleButtonState(createRectangleButton);
          });

          createArrowButton.addEventListener('click', () => {
            // Unpress other button if it's pressed.
            if (createRectangleButton.classList.contains('pressed')) {
              createRectangleButton.classList.remove('pressed');
            }
            toggleButtonState(createArrowButton);
          });


        var viewer = OpenSeadragon({
          id: osd,
          prefixUrl: settings.osd_resources,
          tileSources: settings.image_data,
          showNavigator: true,
          // Initial rotation angle
          degrees: 0,
          // Show rotation buttons
          showRotationControl: true,
          // Enable touch rotation on tactile devices
          gestureSettingsTouch: {
              pinchRotate: true
          }
        });
        
        viewer.addHandler('open', function() {
          settings.overlays.forEach(o => {
            if (o.type == 'highlighted_overlay') {
            var elt = document.createElement("div");
            elt.className = 'highlight';
            viewer.addOverlay({
              element: elt,
              location: new OpenSeadragon.Rect(Number(o.position_x), Number(o.position_y), Number(o.width), Number(o.height))
            });
            }
            else if (o.type == 'fixed_size_overlay') {
              var elt = document.createElement("img");
              elt.src = "/static/images/Red_Arrow_Right.svg";
              elt.width = 20;
              elt.height = 20;
              elt.style.display = "block";  
              elt.className = 'right-arrow-overlay';
              viewer.addOverlay({
                element: elt,
                location: new OpenSeadragon.Point(Number(o.position_x), Number(o.position_y)),
                placement: 'RIGHT',
                checkResize: false});
            }
            else return;
            new OpenSeadragon.MouseTracker({
              element: elt,
              clickHandler: function(e) {
                showDeleteMenu(o.position_x, o.position_y, elt, o.id, viewer);
              },
          });
          });
          }); 

        // Handler for drawing arrow overlays.
        viewer.addHandler("canvas-press", function(event) {
          if (!createArrowButton.classList.contains('pressed')) return;
          let webPoint = event.position;
          arrowPoint = viewer.viewport.pointFromPixel(webPoint);
          create_arrow_overlay({'type': 'fixed_size_overlay', 'position_x': arrowPoint.x, 'position_y': arrowPoint.y}, viewer);
          toggleButtonState(createArrowButton);
          arrowPoint = null;
        });

        // Handler for drawing rectangle overlays.
        viewer.addHandler("canvas-press", function(event) {
          if (!createRectangleButton.classList.contains('pressed')) return;
          let webPoint = event.position;
          startPoint = viewer.viewport.pointFromPixel(webPoint);
          startX = event.position.x;
          startY = event.position.y;
          dragOverlay = document.createElement("div");
          dragOverlay.style.position = "absolute";
          dragOverlay.style.border = "2px solid red";
          dragOverlay.style.background = "transparent";
          dragOverlay.style.pointerEvents = "none";
          dragOverlay.style.left = webPoint.x + "px";
          dragOverlay.style.top = webPoint.y + "px";
          viewer.container.appendChild(dragOverlay);
        });

        // Handler for drawing rectangle overlays.
        viewer.addHandler("canvas-drag", function(event) {
          if (!createRectangleButton.classList.contains('pressed') || !startPoint) return;
          let currentX = event.position.x;
          let currentY = event.position.y;
          let width = Math.abs(currentX - startX);
          let height = Math.abs(currentY - startY);
          dragOverlay.style.width = width + "px";
          dragOverlay.style.height = height + "px";
          dragOverlay.style.left = Math.min(startX, currentX) + "px";
          dragOverlay.style.top = Math.min(startY, currentY) + "px";
        });

        let menu = document.createElement("div");
        menu.id = "overlay-menu-" + settings.location;
        menu.classList.add("overlay-menu");
        menu.innerHTML = '<h3>' + gettext('Do you want to delete this overlay?') + '</h3>';
        let removeOverlayButton = document.createElement('button');
        removeOverlayButton.textContent = gettext('Yes');
        removeOverlayButton.classList.add('delete');
        let closeOverlayMenuButton = document.createElement('button');
        closeOverlayMenuButton.textContent = gettext("No");
        closeOverlayMenuButton.classList.add('close');
        menu.appendChild(removeOverlayButton);
        menu.appendChild(closeOverlayMenuButton);
        viewer.container.appendChild(menu);
        
        // Handler for drawing rectangle overlays.
        viewer.addHandler("canvas-release", function(event) {
          if (!createRectangleButton.classList.contains('pressed') || !startPoint) return;

          let webPoint = event.position;
          let endPoint = viewer.viewport.pointFromPixel(webPoint);

          let x = Math.min(startPoint.x, endPoint.x);
          let y = Math.min(startPoint.y, endPoint.y);
          let width = Math.abs(endPoint.x - startPoint.x);
          let height = Math.abs(endPoint.y - startPoint.y);
          // If the overlay has height and width, try to create it and reset the startPoint.
          if (width > 0 && height > 0) {
            startPoint = null;
            create_rectangle_overlay({'type': 'highlighted_overlay', 'position_x': x, 'position_y': y, 'width': width, 'height': height}, viewer);
          }
          toggleButtonState(createRectangleButton);
          if (dragOverlay) {
            viewer.container.removeChild(dragOverlay);
            dragOverlay = null;
          }
        })

        anno = OpenSeadragon.Annotorious(viewer, {
          locale: 'auto',
          gigapixelMode: false,
          allowEmpty: true,
          formatter: ColorFormatter,
          widgets: [
            ColorSelectorWidget,
            {widget: 'COMMENT', editable: 'MINE_ONLY'},
          ]
        });
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
        $(element).find(toolbar).find('.rect').find('.a9s-toolbar-btn-inner')[0].title = gettext("Add Annotation");
        $(element).find(toolbar).find('.polygon').find('.a9s-toolbar-btn-inner')[0].innerHTML = selectorPolygon;
        $(element).find(toolbar).find('.polygon').find('.a9s-toolbar-btn-inner')[0].title = gettext("Add Annotation");
    });

    function create_arrow_overlay(overlay, viewer){
      $.post(handlerSaveOverlay, JSON.stringify({'overlay': overlay})).done(function(response) {
        if(response.result != 'success'){
          return response.result, response.overlay_id
        }
        else{
          var elt = document.createElement("img");
          elt.src = "/static/images/Red_Arrow_Right.svg";
          elt.width = 20;
          elt.height = 20;
          elt.style.display = "block";  
          elt.className = 'right-arrow-overlay';
          viewer.addOverlay({
            element: elt,
            location: new OpenSeadragon.Point(overlay.position_x, overlay.position_y),
            placement: 'RIGHT',
            checkResize: false});
          new OpenSeadragon.MouseTracker({
            element: elt,
            clickHandler: function(e) {
              showDeleteMenu(overlay.position_x, overlay.position_y, elt, response.overlay_id, viewer);
            },
        });
        }
      })
    };

    function create_rectangle_overlay(overlay, viewer){
      $.post(handlerSaveOverlay, JSON.stringify({'overlay':overlay})).done(function(response) {
        if(response.result != 'success'){
          return response.result, response.overlay_id
        }
        else{
          var elt = document.createElement("div");
          elt.className = 'highlight';
          viewer.addOverlay({
            element: elt,
            location: new OpenSeadragon.Rect(overlay.position_x, overlay.position_y, overlay.width, overlay.height)
          });
          new OpenSeadragon.MouseTracker({
            element: elt,
            clickHandler: function(e) {
              showDeleteMenu(overlay.position_x, overlay.position_y, elt, response.overlay_id, viewer);
            },
        });
          return response.result, response.overlay_id
        }
      });
    };

    // Opens a menu to delete the clicked overlay.
    function showDeleteMenu(x, y, overlay, id, viewer) {   
      let pixelPoint = viewer.viewport.pixelFromPoint(new OpenSeadragon.Point(Number(x), Number(y)));
      menu = document.getElementById("overlay-menu-" + settings.location);

      let width = parseFloat(getComputedStyle(menu)['width']);
      let height = parseFloat(getComputedStyle(menu)['height']);

      // Moves the delete menu if its too close to the edge.
      if (pixelPoint.x + width > viewer.container.clientWidth){
        pixelPoint.x = pixelPoint.x - width;
      }

      // Moves the delete menu if its too close to the edge.
      if (pixelPoint.y + height > viewer.container.clientHeight){
        pixelPoint.y = pixelPoint.y - height;
      }

      menu.style.left = `${pixelPoint.x}px`;
      menu.style.top = `${pixelPoint.y}px`;
      menu.style.display = "block";

      let removeButton = menu.querySelector('.delete');
      removeButton.onclick = () => {
        deleteOverlay(id, overlay);
        menu.style.display = "none";
      };
     
      let closeButton = menu.querySelector('.close');
      closeButton.onclick = () => {
        menu.style.display = "none";
      };
    };

    // Tries to delete an overlay from the database, in case of success it also deletes the overlay from the current view.
    function deleteOverlay(id, overlay){
      $.post(handlerDeleteOverlay, JSON.stringify({'id': id})).done(function(response) {
        if(response.result != 'success'){
          return response.result;
        }
        else{
          overlay.remove();
          return response.result;
        }
      });
    };

    anno.on('createAnnotation', function(annotation) {
      $(element).find('#img_annotation_wrong_label').hide();
      $.post(handlerUrl, JSON.stringify({'annotation':annotation})).done(function(response) {
        if(response.result != 'success'){
          $element.find('#img_annotation_wrong_label')[0].textContent = gettext("Error saving, refresh the page and try again.");
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
          $element.find('#img_annotation_wrong_label')[0].textContent = gettext("Error deleting, refresh the page and try again.");
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
          $element.find('#img_annotation_wrong_label')[0].textContent = gettext("Error editing, refresh the page and try again.");
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
