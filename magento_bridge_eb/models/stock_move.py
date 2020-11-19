# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from .connector import MagentoAPI

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = 'stock.move'

    customer_id = fields.Many2one('res.partner', compute='_compute_customer', store=True)

    @api.depends('sale_line_id')
    def _compute_customer(self):
        for move in self:
            move.customer_id = move.sale_line_id.order_id.partner_id
