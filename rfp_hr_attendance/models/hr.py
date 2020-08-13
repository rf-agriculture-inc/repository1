from odoo import api, fields, models

import logging
_logger = logging.getLogger(__name__)


class HrAttendance(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def update_punch_type(self, data):
        punch_type = data['punch_type']
        _logger.warn(' > > > > > > > > > > > > > > > > > > > > > > > > > > > > > > > > > > > > > > > > > > > > > > > >')
        _logger.warn(punch_type)
        attendance = self.env['hr.attendance'].search([('employee_id', '=', self.id), ('check_out', '=', False)], limit=1)
        _logger.warn(attendance)
        if attendance:
            attendance.employee_punch_type = punch_type or 'general'

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    employee_punch_type = fields.Selection([
        ('general', 'General'),
        ('lunch', 'Lunch'),
        ('break', 'Break'),
    ], string='Clock in/out type', default='general')
