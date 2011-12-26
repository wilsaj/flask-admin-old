
// usage: log('inside coolFunc', this, arguments);
// paulirish.com/2009/log-a-lightweight-wrapper-for-consolelog/
window.log = function(){
  log.history = log.history || [];   // store logs to an array for reference
  log.history.push(arguments);
  if(this.console) console.log( Array.prototype.slice.call(arguments) );
};



// place any jQuery/helper plugins in here, instead of separate, slower script files.

$(document).ready(function() {
    $('.delete-button').click(function() {
        var answer = confirm("Are you sure you want delete this item?");
        if (answer) {
            return true;
        } else {
            return false;
        }
    });
});
