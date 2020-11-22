# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from .connector import MagentoAPI

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    wholesale_markup = fields.Float(string="Wholesale Markup")

    @api.model
    def create(self, vals):
        new_id = super(ProductProduct, self).create(vals)
        new_id.mag_create_product()
        new_id.mag_update_product_price(vals.get('lst_price'))
        return new_id

    def write(self, vals):
        update_rec = super(ProductProduct, self).write(vals)
        self.mag_update_product_price(vals.get('lst_price'))
        return update_rec

    def mag_create_product(self):
        """Create new product in Magento"""
        if self.env.company.magento_bridge and self.default_code:
            api_connector = MagentoAPI(self)
            find_sku_res = api_connector.get_product_by_sku(self.default_code)
            if find_sku_res.status_code == 404:
                res = api_connector.create_new_product(self)
                if res.get('id'):
                    msg = "Product was successfully created in Magento."
                else:
                    msg = res
            elif find_sku_res.status_code == 200:
                msg = f"Product [{self.default_code}] already exist in Magento."
            else:
                msg = find_sku_res.text
            self.message_post(subject='Magento Integration Success', body=msg, message_type='notification')
            self.product_tmpl_id.message_post(subject='Magento Integration Success', body=msg,
                                              message_type='notification')

    def mag_update_product_price(self, new_price):
        """Update Wholesale price in Magento"""
        if self.env.company.magento_bridge and new_price and self.default_code:
            api_connector = MagentoAPI(self)
            if api_connector.get_config(self).update_product_price:
                res = api_connector.update_product_price(self, new_price)
                if res is True:
                    msg = "Wholesale Price was successfully updated in Magento."
                    self.message_post(subject='Magento Integration Success', body=msg, message_type='notification')
