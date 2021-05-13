$.ajax({
    url: $("#probes-graph-container").attr("data-url"),
    dataType: 'json',
    method: "GET",
    success: function (data) {
        $("#probes-graph-container").html(data['graph']);
    },
});
