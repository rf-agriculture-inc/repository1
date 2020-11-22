# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from .connector import MagentoAPI

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    mag_id = fields.Integer(string="Magento ID", copy=False, help="Magento Customer ID")

    @api.constrains('property_product_pricelist')
    def mag_update_customer_group(self):
        """
        Update Customer Group for related customer in Magento
        :return:
        """
        for partner in self:
            if self.env.company.magento_bridge and partner.mag_id and partner.property_product_pricelist.mag_id:
                api_connector = MagentoAPI(self)
                res = api_connector.update_customer_data(partner)
                if res.get('id'):
                    msg = f"Customer Group {partner.property_product_pricelist.name}[{partner.property_product_pricelist.mag_id}]" \
                          f"was successfully added to Customer in Magento."
                    partner.message_post(subject='Magento Integration Success', body=msg, message_type='notification')


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    mag_id = fields.Integer(string="Magento ID", copy=False, readonly=True, help="Magento Cart Item ID")
    mag_quote_id = fields.Integer(string="Magento Quote ID", copy=False, readonly=True, help="Magento Cart Item ID")


class CountryState(models.Model):
    _inherit = 'res.country.state'

    mag_id = fields.Integer(string="Magento ID")
