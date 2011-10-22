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

    function getLabelFor(id){
        return $('label[for="'+id+'"]').text();
    };

    $('.edit_form select:empty')
        .attr('data-placeholder', (
            function(index, attr){
                if (!attr){
                    return 'No '+getLabelFor(this.id)+' available to choose';
                }
            }))
        .attr('disabled', 'disabled')
        .append('<option value="__None"></option>');

    $('.edit_form select')
        .attr('data-placeholder', (
            function(index, attr){
                if (!attr){
                    return 'Choose a '+getLabelFor(this.id)+'...';
                }
            }))
        .chosen({no_results_text: "No results matched"});

});