from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    attendance_state = fields.Selection(selection_add=[('lunch', 'Lunch'), ('break', 'Break')])

    @api.depends('last_attendance_id.work_type_id')
    def _compute_attendance_state(self):
        lunch_type = self.env.ref('rfp_hr_attendance.work_entry_type_lunch')
        break_type = self.env.ref('rfp_hr_attendance.work_entry_type_break')
        for employee in self:
            att = employee.last_attendance_id.sudo()
            if not att or att.check_out:
                employee.attendance_state = 'checked_out'
            elif employee.last_attendance_id.work_type_id == lunch_type:
                employee.attendance_state = 'lunch'
            elif employee.last_attendance_id.work_type_id == break_type:
                employee.attendance_state = 'break'
            else:
                employee.attendance_state = 'checked_in'

    def attendance_manual(self, next_action, entered_pin=None, attendance_type=None):
        if attendance_type == 'lunch':
            work_type = self.env.ref('rfp_hr_attendance.work_entry_type_lunch')
        elif attendance_type == 'break':
            work_type = self.env.ref('rfp_hr_attendance.work_entry_type_break')
        else:
            work_type = self.env.ref('hr_payroll_attendance.work_input_attendance')
        self = self.with_context(work_type_id=work_type.id)
        return super(HrEmployee, self).attendance_manual(next_action, entered_pin=entered_pin)

    def _attendance_action_change(self):
        """ Check In/Check Out action
            Check In: create a new attendance record
            Check Out: modify check_out field of appropriate attendance record
        """
        self.ensure_one()
        action_date = fields.Datetime.now()
        work_type_id = self._context.get('work_type_id', False)

        if self.attendance_state == 'checked_out':
            vals = {
                'employee_id': self.id,
                'check_in': action_date,
                'work_type_id': work_type_id,
            }
            return self.env['hr.attendance'].create(vals)
        attendance = self.env['hr.attendance'].search([('employee_id', '=', self.id), ('check_out', '=', False)], limit=1)
        # TODO: If desired, this segment does let you clock "in" with a different type by ending your old punch
        # if attendance and work_type_id and work_type_id != attendance.work_type_id.id:
        #     attendance.check_out = action_date
        #     vals = {
        #         'employee_id': self.id,
        #         'check_in': action_date,
        #         'work_type_id': work_type_id,
        #     }
        #     return self.env['hr.attendance'].create(vals)
        if attendance:
            attendance.check_out = action_date
        else:
            raise exceptions.UserError(_('Cannot perform check out on %(empl_name)s, could not find corresponding check in. '
                'Your attendances have probably been modified manually by human resources.') % {'empl_name': self.sudo().name, })
        return attendance


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    work_type_id = fields.Many2one('hr.work.entry.type', string='Work Type')
