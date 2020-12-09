# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, tools

_logger = logging.getLogger(__name__)


class FiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    mag_tax_status = fields.Many2one('magento.tax.status')
