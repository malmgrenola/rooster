$(document).ready(function() {
  console.log("Hello JQuery");
});

$(".dropdown-menu li span").click(function() {
  //console.log($(this).text()); // denna skall vi Hämta
  $(this)
    .parents(".input-group")
    .find("#dropdown")
    .html($(this).text());
});
