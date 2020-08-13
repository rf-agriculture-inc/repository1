# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    mag_id = fields.Integer(string="Magento ID", copy=False, help="Magento Customer ID")


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    mag_id = fields.Integer(string="Magento ID", copy=False, readonly=True, help="Magento Cart Item ID")
    mag_quote_id = fields.Integer(string="Magento Quote ID", copy=False, readonly=True, help="Magento Cart Item ID")
