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
                    if all(o.product_uom_qty == o.qty_invoiced for o in order.order_line):
                        payload = {
                            "capture": True,
                            "notify": True
                        }
                    else:
                        items = []
                        for inv_line in self.invoice_line_ids:
                            sale_line_ids = inv_line.mapped('sale_line_ids').filtered(lambda l: l.order_id == order)
                            for order_line in sale_line_ids:
                                if order_line.mag_id:
                                    qty = order_line.invoice_lines.filtered(lambda i: i == inv_line).mapped('quantity')
                                    items.append({
                                            "order_item_id": order_line.mag_id,
                                            "qty": qty[0]
                                        })
                        payload = {"items": items}

                    res = api_connector.create_invoice(self, order.mag_id, payload)
                    if res:
                        try:
                            mag_id = int(res)
                            self.mag_id = f"{self.mag_id},{mag_id}" if self.mag_id else mag_id
                            msg = f'Invoice sent to Magento. Magento Invoice ID: {mag_id}'
                            self.message_post(subject='Magento Integration Success', body=msg,
                                              message_type='notification')
                        except Exception as e:
                            _logger.error(e)
        elif self.type == 'out_refund':
            orders = self.invoice_line_ids.mapped('sale_line_ids').mapped('order_id')
            for order in orders:
                if order.mag_id:
                    items = []
                    return_to_stock_items = []
                    shipping_amount = 0
                    for inv_line in self.invoice_line_ids:
                        sale_line_ids = inv_line.mapped('sale_line_ids').filtered(lambda l: l.order_id == order)
                        for order_line in sale_line_ids:
                            if order_line.mag_id:
                                qty = order_line.invoice_lines.filtered(lambda i: i == inv_line).mapped('quantity')
                                items.append({
                                    "order_item_id": order_line.mag_id,
                                    "qty": qty[0]
                                })
                                return_to_stock_items.append(order_line.mag_id)
                            elif order_line.is_delivery:
                                shipping_amount += order_line.invoice_lines.filtered(lambda i: i == inv_line).mapped('price_subtotal')[0]
                    payload = {
                        "items": items,
                        "notify": 1,
                        "arguments": {
                            "shipping_amount": shipping_amount,
                            "adjustment_positive": 0,
                            "adjustment_negative": 0,
                            "extension_attributes": {
                                "return_to_stock_items": return_to_stock_items,
                            }
                        }
                    }
                    api_connector = MagentoAPI(self)
                    res = api_connector.create_refund(self, order.mag_id, payload)
                    if res:
                        try:
                            mag_id = int(res)
                            self.mag_id = f"{self.mag_id},{mag_id}" if self.mag_id else mag_id
                            msg = f'Credit Memo sent to Magento. Magento Credit Memo ID: {mag_id}'
                            self.message_post(subject='Magento Integration Success', body=msg,
                                              message_type='notification')
                        except Exception as e:
                            _logger.error(e)
