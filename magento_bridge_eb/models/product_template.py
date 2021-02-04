# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from .connector import MagentoAPI

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    wholesale_markup = fields.Float(related='product_variant_ids.wholesale_markup', readonly=False)

    @api.model
    def create(self, vals):
        new_id = super(ProductTemplate, self).create(vals)
        for product in new_id.product_variant_ids:
            product.mag_create_product()
        return new_id

    def unlink(self):
        for product in self:
            product.mag_disable_product()
        res = super(ProductTemplate, self).unlink()

        return res

    @api.constrains('name')
    def mag_update_product_name(self):
        for product in self.product_variant_ids:
            product.mag_update_product_name()

    @api.constrains('list_price')
    def mag_update_product_price(self):
        for product in self.product_variant_ids:
            product.mag_update_product_price()

    def mag_disable_product(self):
        for product in self.product_variant_ids:
            product.mag_disable_product()

    @api.constrains('active')
    def mag_validate_active(self):
        if not self.active:
            self.mag_disable_product()
