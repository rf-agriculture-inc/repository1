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
                try:
                    res = api_connector.update_customer_group(partner)
                    if res is True:
                        msg = f"Customer Group {partner.property_product_pricelist.name}[{partner.property_product_pricelist.mag_id}]" \
                              f"was successfully added to Customer in Magento."
                        partner.message_post(subject='Magento Integration Success', body=msg, message_type='notification')
                except Exception as e:
                    _logger.error(e)
                    msg = "Failed to update Customer group in Magento."
                    partner.message_post(subject='Magento Integration Error', body=msg, message_type='notification')

    @api.constrains('property_account_position_id')
    def mag_update_customer_tax(self):
        """
        Update Customer Tax Status for related customer in Magento
        :return:
        """
        for partner in self:
            if self.env.company.magento_bridge and partner.mag_id and partner.property_account_position_id.mag_tax_status:
                api_connector = MagentoAPI(self)
                try:
                    res = api_connector.update_customer_tax(partner)
                    if res is True:
                        msg = f"Customer Tax Status [{partner.property_account_position_id.mag_tax_status.name}] " \
                              f"was successfully added to Customer in Magento."
                        partner.message_post(subject='Magento Integration Success', body=msg,
                                             message_type='notification')
                except Exception as e:
                    _logger.error(e)
                    msg = f"Failed to update Customer Tax Status in Magento. Reason: {e}"
                    partner.message_post(subject='Magento Integration Error', body=msg, message_type='notification')

    @api.constrains('property_payment_term_id')
    def mag_update_customer_payment_term(self):
        """
        Update Customer Payment Terms for related customer in Magento
        :return:
        """
        for partner in self:
            if self.env.company.magento_bridge and partner.mag_id and partner.property_payment_term_id.mag_payment_terms:
                api_connector = MagentoAPI(self)
                try:
                    res = api_connector.update_customer_payment_terms(partner)
                    if res is True:
                        msg = f"Customer Payment Terms [{partner.property_payment_term_id.mag_payment_terms.name}] " \
                              f"was successfully added to Customer in Magento."
                        partner.message_post(subject='Magento Integration Success', body=msg,
                                             message_type='notification')
                except Exception as e:
                    _logger.error(e)
                    msg = f"Failed to update Customer Payment Terms in Magento. Reason: {e}"
                    partner.message_post(subject='Magento Integration Error', body=msg, message_type='notification')


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    mag_id = fields.Integer(string="Magento ID", copy=False, readonly=True, help="Magento Cart Item ID")
    mag_quote_id = fields.Integer(string="Magento Quote ID", copy=False, readonly=True, help="Magento Cart Item ID")


class CountryState(models.Model):
    _inherit = 'res.country.state'

    mag_id = fields.Integer(string="Magento ID")
