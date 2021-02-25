# -*- coding: utf-8 -*-
from odoo import models, fields
from .connector import MagentoAPI


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
    tax_status_ids = fields.One2many('magento.tax.status', 'mag_config_id', string='Tax Statuses')
    payment_terms_ids = fields.One2many('magento.payment.terms', 'mag_config_id', string='Payment Terms')

    def update_product_prices(self, price_type="fixed", website_id=0, customer_group="Wholesale", group_id=2, quantity=1):
        """
        Update product prices in Magento for products with flag 'mag_to_update'
        """
        products = self.env['product.template'].search([('mag_to_update', '=', True)])
        if products:
            prices = []
            for p in products:
                new_price = p.with_context(pricelist=group_id).price
                p.list_price = new_price
                vals = {
                    "price": new_price,
                    "price_type": price_type,
                    "website_id": website_id,
                    "sku": p.default_code,
                    "customer_group": customer_group,
                    "quantity": quantity,
                }
                prices.append(vals)
            payload = {"prices": prices}
            api_connector = MagentoAPI(self)
            api_connector.mass_update_product_price(payload)
            products.mag_to_update = False


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


class MagentoTaxStatus(models.Model):
    _name = 'magento.tax.status'
    _description = 'Magento Tax Status'

    name = fields.Char(string="Tax Status")
    mag_id = fields.Integer(string="Magento ID")
    mag_config_id = fields.Many2one('magento.bridge.config')


class MagentoPaymentTerms(models.Model):
    _name = 'magento.payment.terms'
    _description = 'Magento Payment Terms'

    name = fields.Char(string="Payment Terms")
    mag_id = fields.Integer(string="Magento ID")
    mag_config_id = fields.Many2one('magento.bridge.config')

