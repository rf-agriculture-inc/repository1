# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, tools

_logger = logging.getLogger(__name__)


class PaymentTerms(models.Model):
    _inherit = 'account.payment.term'

    mag_payment_terms = fields.Many2one('magento.payment.terms', string="Magento Payment Terms")
