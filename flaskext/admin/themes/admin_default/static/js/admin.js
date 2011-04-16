/* Author: 

*/

var i = 1;

// set up jQuery UI widgets
$(function(){
    $('.ui-widget').hover(
        function() { $(this).addClass('ui-state-hover'); },
        function() { $(this).removeClass('ui-state-hover'); }
    );

    $('input.datepicker').datepicker({
        dateFormat: 'yy-mm-dd'
    });
    $('input.datetimepicker').datetimepicker({
        dateFormat: 'yy-mm-dd',
        timeFormat: 'hh:mm:ss'
    });

    $('select[multiple="multiple"]').crossSelect({
        listWidth: 200,
        rows: 15
    });

    $('#clicky').click(test);

});


function test(){
    $.get('/field_trip/get_site_form',
          function(data){
              $('#placeholder').append('<fieldset><legend>Site ' + i + '</legend>' + data + '</fieldset>');
          })

    i+=1;
}
