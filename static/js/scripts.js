$(document).ready(function() {
  // Handle active state navbar
  const paths = window.location.pathname.split("/");
  const firstPath = paths[1];

  if (firstPath === "admin") {
    $(`.nav-link[href="/admin"]`).addClass("active");

    // Handle Admin navbar button states
    $(`.nav-admin[href="/${paths[1]}/${paths[2]}"]`)
      .addClass("btn-light")
      .removeClass("btn-outline-light");

    return;
  }

  if (firstPath === "me") {
    $(`.nav-link[href="/me/overview"]`).addClass("active");
    return;
  }

  $(`.nav-link[href="${window.location.pathname}"]`).addClass("active");
});

// Basket Helpers
$(".basket-on-enter").on("keypress", function(e) {
  if (e.which === 13) {
    $("basket-update").click();
  }
});
