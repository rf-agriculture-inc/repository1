odoo.define('rfp_hr_attendance.my_attendances', function (require) {
"use strict";

var core = require('web.core');
var MyAttendances = require('hr_attendance.my_attendances');

var MyTypedAttendances = MyAttendances.extend({
    events: _.extend({}, MyAttendances.prototype.events, {
        "click .o_hr_attendance_punch_type_lunch": _.debounce(function() {
            this.update_attendance('lunch');
        }, 200, true),
        "click .o_hr_attendance_punch_type_break": _.debounce(function() {
            this.update_attendance('break');
        }, 200, true),
    }),

    update_attendance: function (type) {
        var self = this;
        this._rpc({
                model: 'hr.employee',
                method: 'attendance_manual',
                args: [[self.employee.id], 'hr_attendance.hr_attendance_action_my_attendances', false, type],
            })
            .then(function(result) {
                if (result.action) {
                    self.do_action(result.action);
                } else if (result.warning) {
                    self.do_warn(result.warning);
                }
            });
    },
});

core.action_registry.add('hr_attendance_my_attendances', MyTypedAttendances);

return MyTypedAttendances;

});