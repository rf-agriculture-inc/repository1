odoo.define('rfp_hr_attendance.kiosk_punch_types', function (require) {
    "use strict";

    require('web.dom_ready');
    // var rpc = require('web.rpc');
    //
    // // Doesn't work
    // $(document).ready(function () {
    //     console.log('Document ready function');
    //     var punch_btns = $('.o_hr_attendance_punch_type');
    //     console.log(punch_btns);
    // });
    //
    // // doesn't work
    // $(window).on('load', function () {
    //     console.log('Window on load');
    //
    //     var punch_btns = $('.o_hr_attendance_punch_type');
    //     console.log(punch_btns);
    // });
    //
    // // Also doesn't work
    // window.onload = function () {
    //     console.log('window.onload 1');
    //     window.document.body.onload = doFunction;
    //     var punch_btns = $('.o_hr_attendance_punch_type');
    //     console.log(punch_btns);
    // };
    // function doFunction() {
    //     console.log('window.onload 2');
    // }

    // This gets the elements and could work but is very hacky
    // This was the point that I realized I was off the rails
    //
    // var checkExists = setInterval(function () {
    //     if ($('#kiosk_action_container').length) {
    //         var punch_btns = $('.o_hr_attendance_punch_type');
    //         punch_btns.click(function(){
    //             var punch_type = $(this).data('punch-type');
    //             console.log(punch_type);
    //             rpc.query({
    //                 model: 'hr.employee',
    //                 method: 'update_punch_type',
    //                 args: [{
    //                     'punch_type': punch_type,
    //                 }],
    //             }).then(function(){
    //                 console.log(result)
    //             });
    //         });
    //         clearInterval(checkExists);
    //     }
    // }, 100); // check every 100ms

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var rpc = require('web.rpc');

    var MyPunchType = AbstractAction.extend({
        events: {
            "click .o_hr_attendance_punch_type": _.debounce(function () {

                console.log('Clicked');

                // var type = this.data('punch-type');
                // console.log(type);
                // this.update_attendance_punch_type(type);

            }, 200, true),
        },

        update_attendance_punch_type: function (type) {
            console.log('update_attendance_punch_type');
            var self = this;
            rpc.query({
                model: 'hr.employee',
                method: 'update_punch_type',
                args: [{'punch_type': type}],
            })
                .then(function (result) {
                    console.log('complete');
                });
        },
    });

    core.action_registry.add('hr_attendance_my_punch_type', MyPunchType);

    return MyPunchType;

});
