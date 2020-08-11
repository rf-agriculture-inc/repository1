# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from .connector import MagentoAPI
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    magento_bridge = fields.Boolean(related='company_id.magento_bridge')
    mag_id = fields.Integer(string="Magento ID", readonly=True, copy=False)
    mag_quote_id = fields.Integer(string="Magento Quote ID", readonly=True, copy=False)

    """
    Override Odoo Methods
    """
    def action_confirm(self):
        """
        Send/Create Order in Magento if Magento Bridge activated
        :return: super
        """
        res = super(SaleOrder, self).action_confirm()
        if self.env.company.magento_bridge:
            for so in self:
                so.mag_send_order()
        return res

    """
       Magento Synchronization
    """
    @staticmethod
    def mag_raise_integration_error(msg):
        """
        Display Magento Integration Error
        :param msg: message to show
        :return: display notification
        """
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Magento Integration ERROR',
                'message': msg,
                'sticky': False,
            }
        }

    def mag_send_order(self):
        """
        Steps to create an order are
        1- Create a cart for the customer
        2- Add items to that cart
        3- Add shipping and billing info
        4- Add payment info
        :return:
        """
        if self.mag_id:
            self.mag_update_order()
            msg = f"Update existed order in Magento."
            _logger.error(msg)
            self.message_post(subject='Magento Integration', body=msg,
                              message_type='notification')
            return False
        try:
            # Init Connection
            api_connector = MagentoAPI(self)

            if self.mag_quote_id and self.mag_quote_id != 0:
                quote_id = self.mag_quote_id
            else:
                # Create a cart for the customer
                if not self.partner_id.mag_id or self.partner_id.mag_id == 0:
                    if self.partner_id.email:
                        res = api_connector.get_customer_id_by_email(self.partner_id.email)
                        if res and len(res['items']) > 0:
                            mag_customer_id = res['items'][0]['id']
                            self.partner_id.write({'mag_id': mag_customer_id})
                        else:
                            error_msg = f"Failed to synchronize Sale Order {self.name} with Magento. " \
                                f"Customer {self.partner_id.name} does not exist in Magento."
                            raise ValidationError(error_msg)
                    else:
                        error_msg = f"Failed to synchronize Sale Order {self.name} with Magento. " \
                            f"Customer {self.partner_id.name} has no Magento ID."
                        raise ValidationError(error_msg)
                quote_id = api_connector.create_customers_cart(self.partner_id.mag_id)
                self.mag_quote_id = quote_id

            if not quote_id:
                error_msg = f"Failed to synchronize Sale Order {self.name} with Magento. " \
                    f"Magento Quote ID is {quote_id}"
                raise ValidationError(error_msg)

            # Add items to that cart
            additional_update = False
            order_lines = self.order_line.filtered(lambda r: r.product_id.type != 'service')
            for line in order_lines:
                if (not line.mag_id or line.mag_id == 0) and (not line.mag_quote_id or line.mag_quote_id == 0):
                    cart_item = api_connector.add_carts_items(quote_id, line)
                    if cart_item:
                        line.write({'mag_quote_id': cart_item['item_id']})
                        api_connector.update_cart_item(line)
                        if line.product_uom_qty != cart_item['qty']:
                            error_msg = f"Magento Integration ERROR: Order line with {line.product_id.display_name} " \
                                f"has different values in Magento: Quantity: {cart_item['qty']}"
                            _logger.error(error_msg)
                            self.message_post(subject='Magento Integration ERROR', body=error_msg,
                                              message_type='notification')
                    else:
                        error_msg = f"Magento Integration ERROR: Order line with {line.product_id.display_name} wasn't " \
                            f"synchronized with Magento."
                        _logger.error(error_msg)
                        self.message_post(subject='Magento Integration ERROR', body=error_msg, message_type='notification')
                else:
                    additional_update = True

            # Add shipping and billing info
            api_connector.add_ship_bill_info(quote_id, self)

            # Add payment info
            mag_order_id = api_connector.add_payment_info(quote_id, self)
            if mag_order_id:
                self.mag_id = mag_order_id
                # Update Shipping Price
                self.mag_update_shipping_price(api_connector)
                # Update Item IDs
                res_order_items = api_connector.get_order_items_by_id(mag_order_id)
                if res_order_items.get('items'):
                    for item in res_order_items.get('items'):
                        order_line = self.order_line.filtered(lambda o: o.mag_quote_id == item['quote_item_id'])
                        if order_line:
                            order_line.mag_id = item['item_id']
                msg = f'Order sent to Magento. Magento Order ID: {mag_order_id}'
                self.message_post(subject='Magento Integration Success', body=msg, message_type='notification')
                _logger.info(msg)

                # If order creation in Magento was interrupted and user confirm order second time we need to update
                # existed cart instead of raise quantity
                if additional_update:
                    self.mag_update_order()

        except Exception as e:
            title = 'Magento Integration ERROR'
            error_msg = f'{title}: {e}'
            _logger.exception(error_msg)
            self.message_post(subject=title, body=error_msg, message_type='notification')
            return self.mag_raise_integration_error(error_msg)

    def mag_update_order(self):
        """
        Update Existed in Magento Order
        :return:
        """
        api_connector = MagentoAPI(self)

        # Update Cart Items
        lines_to_update = self.order_line.filtered(lambda l: l.is_delivery is False)
        for line in lines_to_update:
            if line.mag_id:
                api_connector.update_order_item(line)
            else:
                mag_id = api_connector.update_order_item_post(line)
                line.write({'mag_id': mag_id})

        # Update Shipping Price
        self.mag_update_shipping_price(api_connector)

    def mag_update_shipping_price(self, api_connector):
        """
        Update Shipping Cost in Magento
        :param api_connector: connector object
        :return:
        """
        shipping = self.order_line.filtered(lambda r: r.is_delivery is True)
        if shipping:
            shipping_price = shipping[0].price_subtotal
            api_connector.update_shipping_price(self, shipping_price)
        else:
            api_connector.update_shipping_price(self, 0)

