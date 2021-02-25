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
        return new_id

    def unlink(self):
        for product in self:
            product.mag_disable_product()
        res = super(ProductProduct, self).unlink()

        return res

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

    @api.constrains('name')
    def mag_update_product_name(self):
        if self.env.company.magento_bridge and self.default_code:
            api_connector = MagentoAPI(self)
            res = api_connector.update_product_name(self)
            if res.get('id'):
                msg = f"New product name {self.name}  was successfully updated in Magento."
                self.message_post(subject='Magento Integration Success', body=msg, message_type='notification')
                self.product_tmpl_id.message_post(subject='Magento Integration Success', body=msg,
                                                  message_type='notification')

    @api.constrains('standard_price', 'wholesale_markup')
    def mag_update_product_price(self):
        is_import = self.env.context.get('_import_current_module') == '__import__'
        if is_import:
            self.product_tmpl_id.mag_to_update = True
        if self.env.company.magento_bridge and self.default_code and not is_import:
            api_connector = MagentoAPI(self)
            if api_connector.get_config(self).update_product_price:
                pricelists = self.env['product.pricelist'].search([('mag_id', '>', 0)])
                for pricelist_id in pricelists:
                    new_price = self.with_context(pricelist=pricelist_id.id).price

                    # This price assignment here looks very strange, but client's wish is a low
                    self.lst_price = new_price
                    self.product_tmpl_id.list_price = new_price

                    res = api_connector.update_product_price(self, pricelist_id.mag_id, new_price)
                    if res is True:
                        msg = f"{pricelist_id.name} Price was successfully updated to [{new_price}] in Magento."
                        self.message_post(subject='Magento Integration Success', body=msg, message_type='notification')
                        self.product_tmpl_id.message_post(subject='Magento Integration Success', body=msg, message_type='notification')

    def mag_disable_product(self):
        """
        Disable product in Magento
        """
        if self.env.company.magento_bridge and self.default_code:
            api_connector = MagentoAPI(self)
            api_connector.disable_product(self)

    @api.constrains('active')
    def mag_validate_active(self):
        if not self.active:
            self.mag_disable_product()
