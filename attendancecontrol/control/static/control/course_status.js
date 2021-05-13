
$(document).ready(function(){
    const chatSocket = new WebSocket(
        'ws://'
        + window.location.host
        + '/ws/probes/status/course/'
    );

    chatSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        for (course_id in data) {
            if (data[course_id]) {
                $(".course-status-"+course_id+"-ongoing").removeClass('visually-hidden');
                $(".course-status-"+course_id+"-stopped").addClass('visually-hidden');
                $(".course-status-"+course_id+"-unknown").addClass('visually-hidden');
            }
            else {
                $(".course-status-"+course_id+"-ongoing").addClass('visually-hidden');
                $(".course-status-"+course_id+"-stopped").removeClass('visually-hidden');
                $(".course-status-"+course_id+"-unknown").addClass('visually-hidden');
            }
        }
    };

    chatSocket.onclose = function(e) {
        $('span[class^="course-status-"][class*="-ongoing"]').addClass('visually-hidden');
        $('span[class^="course-status-"][class*="-stopped"]').addClass('visually-hidden');
        $('span[class^="course-status-"][class*="-unknown"]').removeClass('visually-hidden');
    };

    chatSocket.addEventListener('open', function (event) {
        setInterval(function(){
            chatSocket.send(JSON.stringify({'get': true}));
        }, 30000); // 30 sec
    });
});
