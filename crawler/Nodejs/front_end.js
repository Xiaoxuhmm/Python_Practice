$("#check-user-button").click(function(){
  "use strict";
  var range = $("#range").val();

  $.ajax({
    url: 'http://localhost:5000' + range,
    type: 'GET'
  });
})