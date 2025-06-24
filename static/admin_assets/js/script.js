// $('tbody').sortable({
//   stop: function( event, ui ) {
//     $("tbody tr").removeClass("aaa");
//     $("tbody tr .name").removeClass("bbb");
    
//     $("tbody tr:first-child").addClass("aaa");
//     $("tbody tr:first-child .name").addClass("bbb");
//   }
// });
// $("tbody tr:first-child").addClass("aaa");
// $("tbody tr:first-child .name").addClass("bbb");




$(function() {
    $( "ul" ).sortable();
    $( "ul" ).disableSelection();
  });




