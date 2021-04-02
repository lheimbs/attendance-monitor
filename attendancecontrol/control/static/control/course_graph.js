// $.ajax({
//     url: $("#probes-graph-container").attr("data-url"),
//     dataType: 'json',
//     method: "GET",
//     success: function (data) {
//         $("#probes-graph-container").html(data['graph']);
//     },
// });

$(document).ready(function(){
        const chatSocket = new WebSocket(
        'ws://'
        + window.location.host
        + '/ws/probes/student/course/'
        + $("#probes-graph-container").attr("data-course-id")
        + '/'
    );

    chatSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        $("#probes-graph-container").html(data.graph);
        chatSocket.close(1000);
    };

    chatSocket.onclose = function(e) {
        console.error('Chat socket closed unexpectedly');
    };

    chatSocket.addEventListener('open', function (event) {
        chatSocket.send(JSON.stringify({
            'course': $("#probes-graph-container").attr("data-course-id")
        }));
    });
});
