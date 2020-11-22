# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from .connector import MagentoAPI

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    wholesale_markup = fields.Float(
        string="Wholesale Markup",
        compute='_compute_wholesale_markup',
        inverse='_set_wholesale_markup'
    )

    @api.depends('product_variant_ids', 'product_variant_ids.wholesale_markup')
    def _compute_wholesale_markup(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.wholesale_markup = template.product_variant_ids.wholesale_markup
        for template in (self - unique_variants):
            template.wholesale_markup = 0.0

    def _set_wholesale_markup(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.wholesale_markup = template.wholesale_markup

    @api.model
    def create(self, vals):
        new_id = super(ProductTemplate, self).create(vals)
        for product in new_id.product_variant_ids:
            product.mag_create_product()
        new_id.mag_update_product_price(vals.get('list_price'))
        return new_id

    def write(self, vals):
        update_rec = super(ProductTemplate, self).write(vals)
        self.mag_update_product_price(vals.get('list_price'))
        return update_rec

    def mag_update_product_price(self, new_price):
        if self.env.company.magento_bridge and new_price and self.default_code:
            api_connector = MagentoAPI(self)
            if api_connector.get_config(self).update_product_price:
                res = api_connector.update_product_price(self, new_price)
                if res is True:
                    msg = "Wholesale Price was successfully updated in Magento."
                    self.message_post(subject='Magento Integration Success', body=msg, message_type='notification')
