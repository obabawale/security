/*
* @Author: D.Jane
* @Email: jane.odoo.sp@gmail.com
*/
odoo.define('limit_login_attempts.init', function (require) {
    "use strict";
    $(document).ready(function () {
        var timer = new Timer();
        var start_value = $('#remaining_time_value').val();
        var error = $('form.oe_login_form > p.alert.alert-danger');
        error.addClass('text-center');
        var remaining_time = $('#remaining_time_container');
        var unblock_message = $('#unblock_message_container');
        if (start_value) {
            setTimeout(function () {
                timer.start({countdown: true, startValues: {seconds: start_value}});
                $('#countdown .remaining_time').html(timer.getTimeValues().toString());
            }, 100);

            timer.addEventListener('secondsUpdated', function (e) {
                $('#countdown .remaining_time').html(timer.getTimeValues().toString());
            });
            timer.addEventListener('targetAchieved', function (e) {
                error.hide();
                remaining_time.hide();
                unblock_message.show();
            });
        }
    });
});