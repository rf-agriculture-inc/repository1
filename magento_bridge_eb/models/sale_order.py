# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from .connector import MagentoAPI
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    magento_bridge = fields.Boolean(related='company_id.magento_bridge')
    mag_id = fields.Integer(string="Magento Database ID", readonly=True, copy=False)
    mag_quote_id = fields.Integer(string="Magento Quote (Cart) ID", readonly=True, copy=False)
    x_studio_customer_po = fields.Char()
    customer_note = fields.Text()
    will_call = fields.Boolean(string="Will Call")
    send_to_magento = fields.Boolean(
        string="Send Order to Magento",
        default=True,
        states={'sale': [('readonly', True)]},
        help="Send Order to Magento on Confirm action. Readonly for confirmed orders."
    )
    order_line_origin = fields.One2many('sale.order.line.origin', 'order_id', string='Order Lines Origin')

    """
    Override Odoo Methods
    """

    def action_confirm(self):
        """
        Send/Create Order in Magento if Magento Bridge activated / Validate routes
        :return: super
        """
        # Set Salesperson
        self.user_id = self.env.user

        # Validate routes
        order_lines = self.order_line
        for line in order_lines:
            if line.check_route_required() and not line.route_id:
                raise UserError(f"Choose Routes for each Storable Product.")

        # Confirm Order
        res = super(SaleOrder, self).action_confirm()

        # Magento Call
        if self.env.company.magento_bridge and self.send_to_magento:
            for so in self:
                so.mag_send_order()
        return res

    def action_cancel(self):
        """
        Cancel Order in Magento if Magento Bridge activated
        :return: super
        """
        # Cancel Order
        res = super(SaleOrder, self).action_cancel()

        # Magento Call
        if self.env.company.magento_bridge and self.mag_id:
            for so in self:
                so.mag_cancel_order()
        return res

    def action_draft(self):
        """
        Remove all info regarding Magento integration
        """
        res = super(SaleOrder, self).action_draft()
        self.write({
            'mag_id': False,
            'mag_quote_id': False,
            'client_order_ref': False,
        })
        for line in self.order_line:
            line.write({
                'mag_id': False,
                'mag_quote_id': False,
            })
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
                        email_arr = self.partner_id.email.replace(' ', '').split(';')
                        res = False
                        for email in email_arr:
                            res = api_connector.get_customer_id_by_email(email)
                            if res and len(res['items']) > 0: break
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

            # list all items in cart
            cart_items = api_connector.get_cart_items(quote_id)
            _logger.info(f"Cart Items to delete: {cart_items}")
            items_to_re_add = []
            for item in cart_items:
                payload = {
                    "cartItem": {
                        "sku": item['sku'],
                        "qty": item['qty'],
                        "price": item['price'],
                    }
                }
                items_to_re_add.append(payload)
                api_connector.remove_cart_item(quote_id, item['item_id'])

            # Add items to that cart
            additional_update = False
            order_lines = self.order_line.filtered(lambda r: r.is_delivery is False and r.product_id.default_code)
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
                        self.message_post(subject='Magento Integration ERROR', body=error_msg,
                                          message_type='notification')
                else:
                    additional_update = True

            # Add coupons to the cart
            for coupon in self.applied_coupon_ids:
                api_connector.add_coupon_to_cart(quote_id, coupon.code)

            # Add shipping and billing info
            api_connector.add_ship_bill_info(quote_id, self)

            # Add payment info
            mag_order_id = api_connector.add_payment_info(quote_id, self)

            # Re-add deleted cart items
            new_quote_id = api_connector.create_customers_cart(self.partner_id.mag_id)
            for payload in items_to_re_add:
                payload['cartItem']['quote_id'] = new_quote_id
                res = api_connector.re_add_carts_items(new_quote_id, payload)
                api_connector.update_re_added_cart_item(new_quote_id, res['item_id'], payload['cartItem']['price'])

            if mag_order_id:
                self.mag_id = mag_order_id
                # Update Shipping Price
                self.mag_update_shipping_price(api_connector)
                # Update Item IDs
                res_order_items = api_connector.get_order_items_by_id(mag_order_id)
                self.client_order_ref = res_order_items.get('increment_id')
                if res_order_items.get('items'):
                    for item in res_order_items.get('items'):
                        sale_order_lines = self.order_line.filtered(lambda o: o.mag_quote_id == item['quote_item_id'])
                        for order_line in sale_order_lines:
                            order_line.mag_id = item['item_id']
                            api_connector.update_order_item(order_line)
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

    def mag_cancel_order(self):
        """
        Cancel Order in Magento Order
        :return:
        """
        api_connector = MagentoAPI(self)
        api_connector.cancel_order(self)

    def mag_update_shipping_price(self, api_connector):
        """
        Update Shipping Cost in Magento
        :param api_connector: connector object
        :return:
        """
        if self.mag_id and self.mag_id > 0:
            shipping_method_code, shipping_carrier_code = api_connector.get_shipping_codes(self)
            payload = {
                "shipping_method": shipping_method_code,
                "order_id": self.mag_id,
            }
            shipping_line = self.order_line.filtered(lambda r: r.is_delivery is True)
            if shipping_line:
                payload['price_excl_tax'] = shipping_line[0].price_subtotal
                payload['price_incl_tax'] = shipping_line[0].price_total
                payload['tax_percent'] = sum(shipping_line[0].tax_id.mapped('amount'))
                payload['description'] = shipping_line.name
                api_connector.update_shipping_price(self, payload)
            else:
                payload['price_excl_tax'] = 0
                payload['price_incl_tax'] = 0
                payload['tax_percent'] = 0
                api_connector.update_shipping_price(self, payload)
