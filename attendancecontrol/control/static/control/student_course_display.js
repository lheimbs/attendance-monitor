
$(document).ready(function(){
    const course_id = $("#student-course-active").attr("data-course-id");

    const statusSocket = new WebSocket(
        window.location.protocol == "https:" ? "wss" : "ws" + '://'
        + window.location.host
        + '/ws/student/attendance/course/'
    );

    statusSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        if (data) {
            $("#student-course-active").removeClass('visually-hidden');
            $("#student-course-not-active").addClass('visually-hidden');
            $("#student-course-active-minutes").text(data['current_present']);
            $("#student-course-active-progress").text(data['current_present_percent']+'%');
            $("#student-course-active-progress").attr('aria-valuenow', data['current_present_percent']);
            $("#student-course-active-progress").removeClass(function (index, className) {
                    return (className.match(/(^|\s)progress-percent-\S+/g) || []).join(' ');
            });
            $("#student-course-active-progress").addClass('progress-percent-'+data['current_present_percent_5']);
        } else {
            $("#student-course-active").addClass('visually-hidden');
            $("#student-course-not-active").removeClass('visually-hidden');
        }
    };

    statusSocket.addEventListener('open', function (event) {
        setInterval(function(){
            statusSocket.send(JSON.stringify({'course': course_id}));
        }, 30000); // 30 sec
    });

    $.ajax({
        url: $("#probes-graph-container").attr("data-url"),
        dataType: 'json',
        method: "GET",
        success: function (data) {
            $("#probes-graph-container").html(data['graph']);
        },
    });
    
});
