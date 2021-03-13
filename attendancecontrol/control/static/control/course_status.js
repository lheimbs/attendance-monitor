function get_courses_states() {
    $.ajax({
        url: $("#course-status-url").attr("data-course-status-url"),
        dataType: 'json',
        method: "GET",
        success: function (data) {
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
        },
        error: function() {
            $('span[class^="course-status-"][class*="-ongoing"]').addClass('visually-hidden');
            $('span[class^="course-status-"][class*="-stopped"]').addClass('visually-hidden');
            $('span[class^="course-status-"][class*="-unknown"]').removeClass('visually-hidden');
        }
    });
}
setInterval(get_courses_states, 60000); // 1 minute