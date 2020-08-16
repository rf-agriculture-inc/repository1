odoo.define('rfp_hr_attendance.kiosk_confirm', function (require) {
"use strict";

var core = require('web.core');
var KioskConfirm = require('hr_attendance.kiosk_confirm');
var KioskConfirmTyped = KioskConfirm.extend({
    events: _.extend({}, KioskConfirm.prototype.events, {
        "click .o_hr_attendance_sign_in_out_icon": _.debounce(function () {
            this.update_attendance();
        }, 200, true),
        "click .o_hr_attendance_punch_type_lunch": _.debounce(function() {
            this.update_attendance('lunch');
        }, 200, true),
        "click .o_hr_attendance_punch_type_break": _.debounce(function() {
            this.update_attendance('break');
        }, 200, true),
        'click .o_hr_attendance_pin_pad_button_ok': _.debounce(function() {
            this.update_attendance_pin();
        }, 200, true),
        'click .o_hr_attendance_pin_pad_button_lunch': _.debounce(function() {
            this.update_attendance_pin('lunch');
        }, 200, true),
        'click .o_hr_attendance_pin_pad_button_break': _.debounce(function() {
            this.update_attendance_pin('break');
        }, 200, true),
    }),
    update_attendance: function (type) {
        var self = this;
        this._rpc({
                model: 'hr.employee',
                method: 'attendance_manual',
                args: [[self.employee_id], this.next_action, false, type],
            })
            .then(function(result) {
                if (result.action) {
                    self.do_action(result.action);
                } else if (result.warning) {
                    self.do_warn(result.warning);
                }
            });
    },
    update_attendance_pin: function (type) {
        var self = this;
        this.$('.o_hr_attendance_pin_pad_button_ok').attr("disabled", "disabled");
        this.$('.o_hr_attendance_pin_pad_button_lunch').attr("disabled", "disabled");
        this.$('.o_hr_attendance_pin_pad_button_break').attr("disabled", "disabled");
        this._rpc({
                model: 'hr.employee',
                method: 'attendance_manual',
                args: [[this.employee_id], this.next_action, this.$('.o_hr_attendance_PINbox').val()],
            })
            .then(function(result) {
                if (result.action) {
                    self.do_action(result.action);
                } else if (result.warning) {
                    self.do_warn(result.warning);
                    self.$('.o_hr_attendance_PINbox').val('');
                    setTimeout( function() { self.$('.o_hr_attendance_pin_pad_button_ok').removeAttr("disabled"); self.$('.o_hr_attendance_pin_pad_button_lunch').removeAttr("disabled"); self.$('.o_hr_attendance_pin_pad_button_break').removeAttr("disabled"); }, 500);
                }
            });
    },
});

core.action_registry.add('hr_attendance_kiosk_confirm', KioskConfirmTyped);
return KioskConfirmTyped;
});