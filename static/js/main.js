$(document).ready(function () {
    $("circle").click(function(){
          let id = $(this).attr('data-tooltip-content').replace('#', '');
          let url = '/report/photoID/' + id;

          if (url !== undefined){
            fetch(url).then(function(response){
                 response.json().then(function (data) {
                    let id = "#"+data.id;
                    let path = data.path;

                    // Seems not be useful because of dynamic change (but in case, keep it)
                    //$(id +" a img").first().attr("src", path);

                    let img_tooltip = $(".tooltipster-content span a img").first();
                    img_tooltip.attr("src", path);

                    if(path.toLowerCase().indexOf('not-available') >= 0){
                        console.log('Found not available')
                        img_tooltip.addClass('img-not-found');
                    }
                 });
            });
          }
    });

    /* For the display of error/info messages*/
    setTimeout(function () {
        $("#msg_block").children().each(function () {
            let field = $(this);
            $.post("/fg/delete/error/id/" + this.id, function () {
                field.fadeOut().remove()
            });
        });

    }, 5000);
});