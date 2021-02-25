# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, tools, api

_logger = logging.getLogger(__name__)


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    mag_id = fields.Integer(string="Magento ID", copy=False)


class PricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    wholesale_markup = fields.Boolean(string="Use Wholesale Markup")

    @api.model
    def create(self, vals):
        new_id = super(PricelistItem, self).create(vals)
        if new_id.applied_on == '1_product' and self.pricelist_id.mag_id > 0:
            new_id.product_tmpl_id.mag_update_product_price()
        return new_id

    def write(self, vals):
        res = super(PricelistItem, self).write(vals)
        if self.applied_on == '1_product' and self.pricelist_id.mag_id > 0:
            self.product_tmpl_id.mag_update_product_price()
        return res
