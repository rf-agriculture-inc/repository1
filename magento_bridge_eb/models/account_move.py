# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from .connector import MagentoAPI

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    mag_id = fields.Char(string="Magento ID", readonly=True, copy=False)

    def action_post(self):
        """Override Method (button Post)"""
        res = super(AccountMove, self).action_post()
        if self.env.company.magento_bridge:
            self.mag_send_invoice()
        return res

    def mag_send_invoice(self):
        """Create Invoice in Magento"""
        if self.mag_id:
            msg = f"Skip to create new invoice in Magento."
            _logger.error(msg)
            self.message_post(subject='Magento Integration ERROR', body=msg,
                              message_type='notification')
            return False
        if self.type == 'out_invoice':
            orders = self.invoice_line_ids.mapped('sale_line_ids').mapped('order_id')
            for order in orders:
                if order.mag_id:
                    api_connector = MagentoAPI(self)
                    res = api_connector.create_invoice(self, order.mag_id)
                    if res:
                        try:
                            mag_id = int(res)
                            self.mag_id = f"{self.mag_id},{mag_id}" if self.mag_id else mag_id
                            msg = f'Invoice sent to Magento. Magento Invoice ID: {mag_id}'
                            self.message_post(subject='Magento Integration Success', body=msg, message_type='notification')
                        except Exception as e:
                            _logger.error(e)
