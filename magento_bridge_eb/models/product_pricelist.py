# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, tools

_logger = logging.getLogger(__name__)


class PricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    wholesale_markup = fields.Boolean(string="Use Wholesale Markup")

    def _compute_price(self, price, price_uom, product, quantity=1.0, partner=False):
        self.ensure_one()
        if self.wholesale_markup and self.compute_price not in ['fixed', 'percentage']:
            convert_to_price_uom = (lambda price: product.uom_id._compute_price(price, price_uom))
            # complete formula
            price = price + (price * product.wholesale_markup / 100)
            price_limit = price
            price = (price - (price * (self.price_discount / 100))) or 0.0
            if self.price_round:
                price = tools.float_round(price, precision_rounding=self.price_round)

            if self.price_surcharge:
                price_surcharge = convert_to_price_uom(self.price_surcharge)
                price += price_surcharge

            if self.price_min_margin:
                price_min_margin = convert_to_price_uom(self.price_min_margin)
                price = max(price, price_limit + price_min_margin)

            if self.price_max_margin:
                price_max_margin = convert_to_price_uom(self.price_max_margin)
                price = min(price, price_limit + price_max_margin)
            return price
        else:
            return super(PricelistItem, self)._compute_price(price, price_uom, product, quantity, partner)
