# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from .connector import MagentoAPI

_logger = logging.getLogger(__name__)


class ProductSupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    @api.model
    def create(self, vals):
        new_id = super(ProductSupplierInfo, self).create(vals)
        new_id.product_tmpl_id.mag_to_update = True
        # self.mag_check_values_for_update({'price': new_id.price}, new_id=new_id)
        return new_id

    def write(self, vals):
        for rec in self:
            price_before = rec.price
            super(ProductSupplierInfo, self).write(vals)
            if price_before != rec.price or vals.get('sequence'):
                self.mag_check_values_for_update(vals)
        return True

    def mag_check_values_for_update(self, vals, new_id=None):
        obj = new_id if new_id else self
        is_price_update = vals.get('price') or vals.get('sequence')
        if not self.env.context.get('import_file') and is_price_update:
            obj.product_tmpl_id.mag_update_product_price()
        elif is_price_update:
            obj.product_tmpl_id.mag_to_update = True


class ProductProduct(models.Model):
    _inherit = 'product.product'

    wholesale_markup = fields.Float(string="Wholesale Markup")

    @api.model
    def create(self, vals):
        if self.env.context.get('wholesale_markup'):
            vals.update({'wholesale_markup': self.env.context.get('wholesale_markup')})
        new_id = super(ProductProduct, self).create(vals)
        new_id.mag_create_product()
        return new_id

    def unlink(self):
        for product in self:
            product.mag_disable_product()
        res = super(ProductProduct, self).unlink()

        return res

    def write(self, vals):
        res = super(ProductProduct, self).write(vals)
        self.mag_check_values_for_update(vals)
        return res

    def mag_check_values_for_update(self, vals):
        is_price_update = vals.get('wholesale_markup')
        if not self.env.context.get('import_file') and is_price_update:
            self.mag_update_product_price()
        elif is_price_update:
            self.product_tmpl_id.mag_to_update = True

    def mag_create_product(self):
        """Create new product in Magento"""
        if self.env.company.magento_bridge and self.default_code:

            # TODO: to refactor - temp solution for new products
            pricelists = self.env['product.pricelist'].search([('mag_id', '>', 0)])
            for pricelist_id in pricelists:
                new_price = self.with_context(pricelist=pricelist_id.id).price

                # This price assignment here looks very strange, but client's wish is a low
                self.lst_price = new_price
                self.product_tmpl_id.list_price = new_price

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
                self.mag_update_product_name()
                self.mag_update_product_price()
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
            if res and res.get('id'):
                msg = f"New product name {self.name}  was successfully updated in Magento."
                self.message_post(subject='Magento Integration Success', body=msg, message_type='notification')
                self.product_tmpl_id.message_post(subject='Magento Integration Success', body=msg,
                                                  message_type='notification')
            else:
                self.mag_create_product()

    def mag_update_product_price(self):
        if self.env.company.magento_bridge and self.default_code:
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
