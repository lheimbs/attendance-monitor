
$(document).ready(function(){
    const statusSocket = new WebSocket(
        'ws://'
        + window.location.host
        + '/ws/probes/status/course/'
    );

    statusSocket.onmessage = function(e) {
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

    statusSocket.onclose = function(e) {
        setTimeout(setCourseStatusUnknown, 1000);
    };

    statusSocket.addEventListener('open', function (event) {
        setInterval(function(){
            statusSocket.send(JSON.stringify({'get': true}));
        }, 3000); // 30 sec
    });
});

function setCourseStatusUnknown() {
    $('span[class^="course-status-"][class*="-ongoing"]').addClass('visually-hidden');
    $('span[class^="course-status-"][class*="-stopped"]').addClass('visually-hidden');
    $('span[class^="course-status-"][class*="-unknown"]').removeClass('visually-hidden');
};