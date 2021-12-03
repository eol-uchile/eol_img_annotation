/*
        .-"-.
       /|6 6|\
      {/(_0_)\}
       _/ ^ \_
      (/ /^\ \)-'
       ""' '""
*/


function ImgAnnotationStudioXBlock(runtime, element) {

    $(element).find('.save-button-img_annotation').bind('click', function(eventObject) {
        eventObject.preventDefault();
        var handlerUrl = runtime.handlerUrl(element, 'studio_submit');
        var data = {
            'display_name': $(element).find('input[name=display_name]').val(),
            'image_url': $(element).find('input[name=image_url]').val(),
            'puntajemax': $(element).find('input[name=puntajemax]').val(),
            'header_text': $(element).find('textarea[name=header_text]').val(),
        };
        if ($.isFunction(runtime.notify)) {
            runtime.notify('save', {state: 'start'});
        }
        $.post(handlerUrl, JSON.stringify(data)).done(function(response) {
            if (response.result == 'success' && $.isFunction(runtime.notify)) {
                runtime.notify('save', {state: 'end'});
                var osd = document.getElementById('openseadragon-scripts');
                if (osd == null){
                    window.location.reload();
                }
            }
            else {
                runtime.notify('error',  {
                    title: 'Error: Falló en Guardar',
                    message: 'Revise los campos si estan correctos.'
                });
            }
        });
    });
    
    $(element).find('.cancel-button-img_annotation').bind('click', function(eventObject) {
        eventObject.preventDefault();
        runtime.notify('cancel', {});
    });

}