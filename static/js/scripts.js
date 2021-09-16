$(document).ready(function() {
  console.log("Hello JQuery");
});

// Search Helpers
$(".dropdown-menu li span").click(function() {
  $(this)
    .parents(".input-group")
    .find("#dropdown")
    .html($(this).text());
});

// Basket Helpers
$(".basket-on-enter").on("keypress", function(e) {
  if (e.which === 13) {
    $("basket-update").click();
  }
});
