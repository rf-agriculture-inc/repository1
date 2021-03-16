# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class RFAProductProduct(models.Model):
    _inherit = 'product.product'

    wholesale_markup = fields.Float(string="Wholesale Markup")

    def price_compute(self, price_type, uom=False, currency=False, company=False):
        if price_type == 'purchase_price':
            products = self
            prices = dict.fromkeys(self.ids, 0.0)
            for product in products:
                prices[product.id] = product.product_tmpl_id.purchase_price or product.product_tmpl_id.list_price
        else:
            prices = super(RFAProductProduct, self).price_compute(price_type, uom, currency, company)
        return prices
