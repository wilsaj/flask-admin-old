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
        showSecond: true,
        dateFormat: 'yy-mm-dd',
        timeFormat: 'hh:mm:ss'
    });

    $('input.timepicker').timepicker({
        timeFormat: 'hh:mm:ss',
        showSecond: true
    });

    $('select[multiple="multiple"]').crossSelect({
        listWidth: 200,
        rows: 15
    });
});

