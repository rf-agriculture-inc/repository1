# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from .connector import MagentoAPI

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def create(self, vals):
        new_id = super(ProductProduct, self).create(vals)
        new_id.mag_update_product_price(vals.get('lst_price'))
        return new_id

    def write(self, vals):
        update_rec = super(ProductProduct, self).write(vals)
        self.mag_update_product_price(vals.get('lst_price'))
        return update_rec

    def mag_update_product_price(self, new_price):
        if self.env.company.magento_bridge and new_price and self.default_code:
            api_connector = MagentoAPI(self)
            if api_connector.get_config(self).update_product_price:
                res = api_connector.update_product_price(self, new_price)
                if res is True:
                    msg = "Wholesale Price was successfully updated in Magento."
                    self.message_post(subject='Magento Integration Success', body=msg, message_type='notification')
