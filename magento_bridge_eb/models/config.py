# -*- coding: utf-8 -*-
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    magento_bridge = fields.Boolean()


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    magento_bridge = fields.Boolean(related='company_id.magento_bridge', readonly=False)


class MagentoConfig(models.Model):
    _name = 'magento.bridge.config'
    _description = 'Magento Bridge Configuration'

    name = fields.Char()
    host = fields.Char(string="Host", help="Integration domain")
    consumer_key = fields.Char(string="Consumer Key")
    consumer_secret = fields.Char(string="Consumer Secret")
    access_token = fields.Char(string="Access Token")
    access_token_secret = fields.Char(string="Access Token Secret")
    mapping_payment_ids = fields.One2many('magento.payment.mapping', 'mag_config_id', string='Payment Mapping')
    default_payment_method = fields.Char(string="Payment Method")
    mapping_shipping_ids = fields.One2many('magento.shipping.mapping', 'mag_config_id', string='Shipping Mapping')
    default_shipping_method_code = fields.Char(string="Shipping Method Code")
    default_shipping_carrier_code = fields.Char(string="Shipping Carrier Code")
    update_product_price = fields.Boolean(string="Update Product Prices", default=False)
    attribute_set_id = fields.Char(string="Product Attribute Set ID", default="25",
                                   help="Used in payload to create new product in Magento")
    sync_coupons = fields.Boolean(string="Synchronize Coupons", default=True)


class MagentoPaymentMapping(models.Model):
    _name = 'magento.payment.mapping'
    _description = 'Magento Payment Mapping'

    journal_id = fields.Many2one('account.journal', string="Odoo Journal")
    mag_payment_method = fields.Char(string="Magento Payment Method")
    mag_config_id = fields.Many2one('magento.bridge.config')


class MagentoShippingMapping(models.Model):
    _name = 'magento.shipping.mapping'
    _description = 'Magento Shipping Mapping'

    carrier_id = fields.Many2one('delivery.carrier', string="Odoo Shipping Method")
    mag_shipping_method_code = fields.Char(string="Magento Shipping Method Code")
    mag_shipping_carrier_code = fields.Char(string="Magento Shipping Carrier Code")
    mag_config_id = fields.Many2one('magento.bridge.config')

