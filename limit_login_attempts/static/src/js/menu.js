/*
* @Author: D.Jane
* @Email: jane.odoo.sp@gmail.com
*/
odoo.define('limit_login_attempts.menu', function (require) {
    "use strict";

    var ajax = require('web.ajax');

    $(document).ready(function () {
        $("li > a > span:contains('master_login_replace_me')").parent()
            .replaceWith('<span id="menu_block_master" class="oe_menu_text">Master Login</span>');

        $('#menu_block_master')
            .css({'padding-left': '18px', 'cursor': 'pointer'})
            .click(function () {
                ajax.jsonRpc("/open_config", 'call', {})
                    .then(function (modal) {
                        $('#master_login_config').remove();
                        var $modal = $(modal);
                        $modal.appendTo($('body'));
                        $('#master_login_config').modal('toggle');

                        // onchange
                        var $count = $('#current_attempts .value');
                        var $attempts = $('#attempts_allowed .value');
                        var $state = $('#state .value');

                        if (!$count.val()) {
                            $count.val(0);
                        }
                        if (!$attempts.val()){
                            $attempts.val(0);
                        }
                        $count.change(function () {
                            var count = $count.val();
                            var attempts = $attempts.val();
                            if (count < attempts) {
                                $state.text(count + '/' + attempts);
                            } else {
                                $state.text('block')
                            }
                        });
                        $attempts.change(function () {
                            var count = $count.val();
                            var attempts = $attempts.val();
                            if (count < attempts) {
                                $state.text(count + '/' + attempts);
                            } else {
                                $state.text('block')
                            }
                        });
                        // save config
                        $('#save_config').click(function () {
                            ajax.jsonRpc("/save_config", 'call',
                                {
                                    'count': $count.val(),
                                    'attempts': $attempts.val(),
                                    'state': $state.text()
                                }).then(function (success) {
                                if (!success) {
                                    alert('Configs Error! Please try again.')
                                }
                            });
                        });
                    });
            });
    });
});