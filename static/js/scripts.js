$(document).ready(function() {
  // Handle active state navbar
  const firstPath = window.location.pathname.split("/")[1];

  if (firstPath === "admin") {
    $(`.nav-link[href="/admin"]`).addClass("active");
    return;
  }

  if (firstPath === "me") {
    $(`.nav-link[href="/me/overview"]`).addClass("active");
    return;
  }

  $(`.nav-link[href="${window.location.pathname}"]`).addClass("active");
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
