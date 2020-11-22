# -*- coding: utf-8 -*-
import logging
import requests
import json
from datetime import datetime as dt
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MagentoAPI(object):
    """
    Documentation:
    https://devdocs.magento.com/guides/v2.3/get-started/authentication/gs-authentication-token.html
    https://devdocs.magento.com/redoc/2.3/admin-rest-api.html
    """

    def __init__(self, odoo):
        self.config = self.get_config(odoo)

    """
    Base Methods
    """
    @staticmethod
    def get_config(self):
        """
        Get Odoo-Magento Config Object
        :param self: Odoo Environment Object
        :return: magento.bridge.config - configuration object
        """
        config_ref = self.env['ir.model.data'].search([
            ('name', '=', 'magento_bridge_config'),
            ('model', '=', 'magento.bridge.config'),
        ], limit=1)
        return self.env['magento.bridge.config'].browse(config_ref.res_id)

    def get_header(self):
        """
        Generate Header for API Calls
        :return: dict - API Call Header
        """
        if not self.config.access_token:
            raise UserError('Failed to make API call. Access Token is required.')
        return {
            'Authorization': f'Bearer {self.config.access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

    def search(self, model, filters):
        """
        Base Magento API Search
        :param model: string - Magento Search Model
        :param filters: dict - request params
        :return: json response or None
        """
        url = f'{self.config.host}/rest/all/V1/{model}/search'
        response = requests.get(url, headers=self.get_header(), params=filters)
        return self.process_response(response)

    def put(self, model, id, payload):
        """
        Magento PUT API Call
        :param model: string - Magento Model
        :param id: integer - object ID
        :param payload: dict - request data
        :return: json response or None
        """
        url = f'{self.config.host}/rest/V1/{model}/{id}'
        response = requests.put(url, headers=self.get_header(), data=json.dumps(payload))
        return self.process_response(response)

    def post(self, model, payload):
        """
        Magento POST API Call
        :param model: string - Magento Model
        :param payload: request data
        :return: json response or None
        """
        url = f'{self.config.host}/rest/V1/{model}'
        _logger.info(f'API Call URL: {url}')
        response = requests.post(url, headers=self.get_header(), data=json.dumps(payload))
        return self.process_response(response)

    """
    Magento Specific Calls
    """
    """
    ORDERS
    """
    def get_customer_id_by_email(self, email):
        """
        Get Magento Customer ID by email
        :param email: string - Email
        :return: Magento Customer ID or None
        """
        filters = {
            "searchCriteria[filterGroups][0][filters][0][field]": "email",
            "searchCriteria[filterGroups][0][filters][0][value]": email,
            "searchCriteria[filterGroups][0][filters][0][condition_type]": "like",
        }
        return self.search('customers', filters)

    def update_customer_data(self, customer):
        """
        Update Customer Data in Magento
        :param customer: res.partner
        :return:
        """
        url = f'{self.config.host}/rest/V1/customers/{customer.mag_id}'
        # TODO: investigate why email, firstname, lastname is required
        payload = {"customer": {
            "id": customer.mag_id,
            # "email": "david.d@decofoodservice.com",
            # "firstname": "David Fisrt",
            # "lastname": "David Last",
            # "website_id": 1,
            "group_id": customer.property_product_pricelist.mag_id,
        }}
        _logger.info(f'API Call URL: {url}, Payload: {payload}')
        response = requests.put(url, headers=self.get_header(), data=json.dumps(payload))
        return self.process_response(response, customer)

    def create_customers_cart(self, customer_id):
        """
        Create a cart for the customer
        :param customer_id: integer - Customer ID
        :return: json - response or None
        """
        url = f'{self.config.host}/rest/V1/customers/{customer_id}/carts'
        _logger.info(f'API Call URL: {url}')
        response = requests.post(url, headers=self.get_header())
        return self.process_response(response)

    def get_cart_items(self, quote_id):
        """
        Create a cart for the customer
        :param quote_id: integer - Cart ID
        :return: json - response or None
        """
        url = f'{self.config.host}/rest/V1/carts/{quote_id}/items'
        _logger.info(f'API Call URL: {url}')
        response = requests.get(url, headers=self.get_header())
        return self.process_response(response)

    def add_carts_items(self, quote_id, line):
        """
        Add items to the cart
        :param quote_id: Magento Quotation ID
        :param line: Odoo Order Line
        :return: json - response or None
        """
        url = f'{self.config.host}/rest/V1/carts/{quote_id}/items'
        _logger.info(f'API Call URL: {url}')
        payload = {
            "cartItem": {
                "sku": line.product_id.default_code,
                "qty": line.product_uom_qty,
                "price": line.price_unit,
                "quote_id": quote_id,
            }
        }
        response = requests.post(url, headers=self.get_header(), data=json.dumps(payload))
        if response.status_code == 404:
            new_product_res = self.create_new_product(line.product_id)
            if new_product_res.get('id'):
                return self.add_carts_items(quote_id, line)
        else:
            return self.process_response(response, line.order_id)

    def remove_cart_item(self, quote_id, item_id):
        """
        Remove Order Item
        :param quote_id: Cart ID
        :param item_id: Item ID
        :return: json - response or None
        """
        url = f'{self.config.host}/rest/V1/carts/{quote_id}/items/{item_id}'
        _logger.info(f'API Call URL: {url}')
        response = requests.delete(url, headers=self.get_header())
        return self.process_response(response)

    def re_add_carts_items(self, quote_id, payload):
        """
        Add items to the cart
        :param quote_id: Magento Quotation ID
        :param payload: request payload
        :return: json - response or None
        """
        url = f'{self.config.host}/rest/V1/carts/{quote_id}/items'
        _logger.info(f'API Call URL: {url}')
        response = requests.post(url, headers=self.get_header(), data=json.dumps(payload))
        return self.process_response(response)

    def add_ship_bill_info(self, quote_id, order):
        """
        Add shipping and billing info
        :param quote_id: Magento Quotation ID
        :param order: Odoo Sale Order
        :return: json - response or None
        """
        url = f'{self.config.host}/rest/V1/carts/{quote_id}/shipping-information'

        # Prepare payload
        ship_address = order.partner_shipping_id
        bill_address = order.partner_invoice_id
        ship_company_name = ship_address.name if ship_address.company_type == 'company' else ship_address.company_name or ''
        bill_company_name = bill_address.name if bill_address.company_type == 'company' else bill_address.company_name or ''
        ship_name = ship_address.name or ship_address.parent_id.name
        ship_name_split = ship_name.split(' ')
        ship_firstname = ship_name_split[0]
        ship_lastname = ' '.join(ship_name_split[1:]) or '-'
        bill_name = bill_address.name or bill_address.parent_id.name
        bill_name_split = bill_name.split(' ')
        bill_firstname = bill_name_split[0]
        bill_lastname = ' '.join(bill_name_split[1:]) or '-'
        ship_street = ship_address.street or ''
        if ship_address.street2:
            ship_street = f'{ship_street}, {ship_address.street2}'
        bill_street = bill_address.street or ''
        if bill_address.street2:
            bill_street = f'{bill_street}, {bill_address.street2}'

        shipping_method_code, shipping_carrier_code = self.get_shipping_codes(order)

        payload = {
            "addressInformation": {
                "shippingAddress": {
                    "region": ship_address.state_id.name if ship_address.state_id else '',
                    "region_id": ship_address.state_id.mag_id if ship_address.state_id else 0,
                    "country_id": ship_address.country_id.code if ship_address.country_id else '',
                    "street": [
                        ship_street
                    ],
                    "company": ship_company_name,
                    "telephone": ship_address.mobile or ship_address.phone,
                    "postcode": ship_address.zip,
                    "city": ship_address.city,
                    "firstname": ship_firstname,
                    "lastname": ship_lastname,
                    "email": ship_address.email,
                    "prefix": "address_",
                    "region_code": ship_address.state_id.code if ship_address.state_id else '',
                    "sameAsBilling": 1 if ship_address.id == bill_address.id else 0
                },
                "billingAddress": {
                    "region": bill_address.state_id.name if bill_address.state_id else '',
                    "region_id": bill_address.state_id.mag_id if bill_address.state_id else 0,
                    "country_id": bill_address.country_id.code if bill_address.country_id else '',
                    "street": [
                        bill_street
                    ],
                    "company": bill_company_name,
                    "telephone": bill_address.mobile or bill_address.phone,
                    "postcode": bill_address.zip,
                    "city": bill_address.city,
                    "firstname": bill_firstname,
                    "lastname": bill_lastname,
                    "email": bill_address.email,
                    "prefix": "address_",
                    "region_code": bill_address.state_id.code if bill_address.state_id else '',
                },
                "shipping_method_code": shipping_method_code,
                "shipping_carrier_code": shipping_carrier_code
            }
        }

        _logger.info(f'API Call URL: {url}\nPayload: {payload}')
        response = requests.post(url, headers=self.get_header(), data=json.dumps(payload))
        return self.process_response(response, order)

    def add_payment_info(self, quote_id, order):
        """
        Add payment info
        :param quote_id: Magento Quotation ID
        :param order: Odoo Sale Order
        :return: Magento Order ID
        """
        url = f'{self.config.host}/rest/V1/carts/{quote_id}/order'
        _logger.info(f'API Call URL: {url}')
        # payment_method = self.get_payment_method(order)
        payment_method = self.config.default_payment_method
        method_code, carrier_code = self.get_shipping_codes(order)
        payload = {
            "paymentMethod": {
                "method": payment_method,
                "AdditionalData": {
                    "fromOdoo": "true"
                }
            },
            "shippingMethod": {
                "method_code": method_code,
                "carrier_code": carrier_code,
                "additionalProperties": {}
            }
        }
        response = requests.put(url, headers=self.get_header(), data=json.dumps(payload))
        return self.process_response(response, order)

    def update_cart_item(self, line):
        """
        Update Order Line Price Unit in Magento
        :param line: Odoo Order Line
        :return: json - response or None
        """
        url = f'{self.config.host}/rest/V1/carts/updateCartItem/{line.order_id.mag_quote_id}/{line.mag_quote_id}/{line.price_unit}'
        _logger.info(f'API Call URL: {url}')
        response = requests.put(url, headers=self.get_header())
        return self.process_response(response, line.order_id)

    def update_re_added_cart_item(self, quote_id, item_id, price):
        """
        Update Order Line Price Unit in Magento
        :param quote_id: Cart ID
        :param item_id: Item ID
        :param price: New price
        :return: json - response or None
        """
        url = f'{self.config.host}/rest/V1/carts/updateCartItem/{quote_id}/{item_id}/{price}'
        _logger.info(f'API Call URL: {url}')
        response = requests.put(url, headers=self.get_header())
        return self.process_response(response)

    def update_shipping_price(self, order_id, payload):
        """
        Update Customer Shipping Price
        :param order_id: Order object
        :param payload: data to update
        :return: json - response or None
        """
        url = f'{self.config.host}/rest/all/V1/order/{order_id.mag_id}/addshippingprice'
        _logger.info(f'API Call URL: {url}, payload: {payload}')
        response = requests.put(url, headers=self.get_header(), data=json.dumps(payload))
        return self.process_response(response, order_id)

    def get_order_items_by_id(self, order_id):
        """
        Get Magento Order Info
        :param order_id: Magento Order ID
        :return: json - response or None
        """
        url = f'{self.config.host}/rest/V1/orders/{order_id}'
        _logger.info(f'API Call URL: {url}')
        response = requests.get(url, headers=self.get_header())
        return self.process_response(response)

    def create_shipment(self, picking):
        """
        Create new Shipment for given Order
        :param picking: Odoo Stock Picking Object
        :return: json - response or None
        """
        url = f'{self.config.host}/rest/V1/order/{picking.sale_id.mag_id}/ship'
        items = []
        for move_line_id in picking.move_line_ids:
            order_item_id = move_line_id.move_id.sale_line_id.mag_id
            qty = move_line_id.qty_done
            items.append({
                "order_item_id": order_item_id,
                "qty": qty,
            })
        method_code, carrier_code = self.get_shipping_codes(picking.sale_id)

        if picking.carrier_tracking_ref:
            payload = {
                "comment": {
                  "comment": picking.carrier_id.name,
                  "is_visible_on_front": 0,
                },
                "items": items,
                "tracks": [{
                    "carrier_code": carrier_code,
                    "title": picking.carrier_id.name,
                    "track_number": picking.carrier_tracking_ref,
                }]
            }
        else:
            payload = {
                "items": items,
            }

        _logger.info(f'API Call URL: {url}\nPayload: {payload}')
        response = requests.post(url, headers=self.get_header(), data=json.dumps(payload))
        return self.process_response(response, picking)

    def update_order_item(self, order_line):
        """
        Update Existed Order Item
        :param order_line: Sale Order Line
        :return: json - response or None
        """
        url = f'{self.config.host}/rest/V1/order/{order_line.order_id.mag_id}/updateorderitem'
        _logger.info(f'API Call URL: {url}')
        tax_percent = sum(order_line.tax_id.mapped('amount'))
        price_incl_tax = round(order_line.price_unit * (1 + (tax_percent / 100)), 2)

        discount_amount = round(order_line.price_unit * order_line.product_uom_qty * order_line.discount / 100, 2) if order_line.discount > 0 else 0
        if discount_amount == 0:
            subtotal = order_line.price_subtotal
            subtotal_incl_tax = order_line.price_total
        else:
            subtotal = round(order_line.price_subtotal / (1 - order_line.discount / 100), 2)
            subtotal_incl_tax = round(order_line.price_total / (1 - order_line.discount / 100), 2)

        payload = {
            "order_id": order_line.order_id.mag_id,
            "item": {
                order_line.mag_id: {
                    "item_id": order_line.mag_id,
                    "item_type": "order",
                    "price": order_line.price_unit,
                    "fact_qty": order_line.product_uom_qty,
                    "price_incl_tax": price_incl_tax,
                    # "subtotal": order_line.price_subtotal,
                    "subtotal": subtotal,
                    # "subtotal_incl_tax": order_line.price_total,
                    "subtotal_incl_tax": subtotal_incl_tax,
                    "tax_amount": round(order_line.price_total - order_line.price_subtotal, 2),
                    "tax_percent": tax_percent,
                    "discount_amount": discount_amount,
                    "discount_percent": order_line.discount,
                }
            }
        }
        response = requests.put(url, headers=self.get_header(), data=json.dumps(payload))
        return self.process_response(response, order_line.order_id)

    def update_order_item_post(self, order_line):
        """
        Create New Order Item
        :param order_line: Sale Order Line
        :return: json - response or None
        """
        url = f'{self.config.host}/rest/V1/order/{order_line.order_id.mag_id}/updateorderitem'
        _logger.info(f'API Call URL: {url}')
        tax_percent = sum(order_line.tax_id.mapped('amount'))
        discount_amount = round(order_line.price_unit * order_line.product_uom_qty * order_line.discount / 100, 2) if order_line.discount > 0 else 0
        if discount_amount == 0:
            subtotal = order_line.price_subtotal
            subtotal_incl_tax = order_line.price_total
        else:
            subtotal = round(order_line.price_subtotal / (1 - order_line.discount / 100), 2)
            subtotal_incl_tax = round(order_line.price_total / (1 - order_line.discount / 100), 2)

        payload = {
            "order_id": order_line.order_id.mag_id,
            "item": {
                order_line.product_id.default_code: {
                    "price": order_line.price_unit,
                    "price_incl_tax": round(order_line.price_unit * (1 + (tax_percent / 100)), 2),
                    "fact_qty": order_line.product_uom_qty,
                    # "subtotal": order_line.price_subtotal,
                    "subtotal": subtotal,
                    # "subtotal_incl_tax": order_line.price_total,
                    "subtotal_incl_tax": subtotal_incl_tax,
                    "tax_amount": round(order_line.price_total - order_line.price_subtotal, 2),
                    "tax_percent": tax_percent,
                    "discount_amount": discount_amount,
                    "discount_percent": order_line.discount,
                }
            }
        }
        response = requests.post(url, headers=self.get_header(), data=json.dumps(payload))
        return self.process_response(response, order_line.order_id)

    def remove_order_item(self, order, mag_id):
        """
        Remove Order Item
        :param order: Sale Order
        :param mag_id: Sale Order Line Magento ID
        :return: json - response or None
        """
        url = f'{self.config.host}/rest/V1/order/{order.mag_id}/updateorderitem'
        _logger.info(f'API Call URL: {url}')
        payload = {
            "order_id": order.mag_id,
            "item": {
                mag_id: {
                    "item_id": mag_id,
                    "item_type": "order",
                    "action": "remove"
                }
            }
        }
        response = requests.delete(url, headers=self.get_header(), data=json.dumps(payload))
        return self.process_response(response, order)

    def cancel_order(self, order):
        """
        Remove Order Item
        :param order: Sale Order
        :return: json - response or None
        """
        url = f'{self.config.host}/rest/V1/orders/{order.mag_id}/cancel'
        _logger.info(f'API Call URL: {url}')
        response = requests.post(url, headers=self.get_header())
        return self.process_response(response, order)

    """
    INVOICES
    """
    def create_invoice(self, invoice, order_id, payload):
        """
        Create Invoice for given Order
        :param invoice: Account Move Object
        :param order_id: Magento Order ID
        :param payload: invoice data
        :return: json - response or None
        """
        url = f'{self.config.host}/rest/V1/order/{order_id}/invoice'
        _logger.info(f'API Call URL: {url}')
        response = requests.post(url, headers=self.get_header(), data=json.dumps(payload))
        return self.process_response(response, invoice)

    def create_refund(self, invoice, order_id, payload):
        """
        Create Credit Note (Refund) for given Order
        :param invoice: Account Move Object
        :param order_id: Magento Order ID
        :param payload: refund data
        :return: json - response or None
        """
        url = f'{self.config.host}/rest/default/V1/order/{order_id}/refund'
        _logger.info(f'API Call URL: {url}')
        response = requests.post(url, headers=self.get_header(), data=json.dumps(payload))
        return self.process_response(response, invoice)

    """
    PRODUCTS
    """
    def update_product_price(self, product, customer_group_id, new_price):
        """
        Update Product Base Price
        :param product: product.product
        :param customer_group_id: Magento Customer Group ID
        :param new_price: new price
        :return: json - response or None
        """
        url = f'{self.config.host}/rest/all/V1/products/{product.default_code}/group-prices/{customer_group_id}/tiers/1/price/{new_price}'
        _logger.info(f'API Call URL: {url}')
        response = requests.post(url, headers=self.get_header())
        return self.process_response(response, product)

    def create_new_product(self, product_id):
        """
        Create New Product
        :param product_id: product (product.product)
        :return: json - response or None
        """
        url = f'{self.config.host}/rest/default/V1/products'
        payload = {
            "product": {
                "sku": product_id.default_code,
                "name": product_id.name,
                "price": product_id.lst_price,
                "weight": product_id.weight,
                "attribute_set_id": self.config.attribute_set_id,
                "visibility": 1,
            }
        }
        _logger.info(f'API Call URL: {url}; Payload: {payload}')
        response = requests.post(url, headers=self.get_header(), data=json.dumps(payload))
        return self.process_response(response)

    def get_product_by_sku(self, sku):
        """
        Get Magento Product by sku
        :param sku: string - Product sku
        :return: Magento Product ID or None
        """
        url = f'{self.config.host}/rest/all/V1/products/{sku}'
        response = requests.get(url, headers=self.get_header())
        return response

    """
    COUPONS
    """
    def create_sale_rule(self, name):
        """
        Save sales rule
        :param name: rule name (string)
        :return: json - response or None
        """
        url = f'{self.config.host}/rest/all/V1/salesRules'
        payload = {
            "rule": {
                "name": name,
                "is_active": 1,
                "coupon_type": "SPECIFIC_COUPON",
                "uses_per_coupon": 1,
                "use_auto_generation": 0,
                "from_date": f'{dt.now().strftime("%m")}/{dt.now().strftime("%d")}/{dt.now().strftime("%Y")}',
                "website_ids": [
                    1
                ],
                "customer_group_ids": [
                    0, 1, 2, 3
                ],
            }
        }
        _logger.info(f'API Call URL: {url}')
        response = requests.post(url, headers=self.get_header(), data=json.dumps(payload))
        return self.process_response(response)

    def create_coupon(self, rule_id, code):
        """
        Create coupon for a rule
        :param rule_id: rule ID
        :param code: coupon code
        :return: json - response or None
        """
        url = f'{self.config.host}/rest/all/V1/coupons'
        payload = {
            "coupon": {
                "rule_id": rule_id,
                "code": code,
                "is_primary": 1,
                "times_used": 1,
                "usage_limit": 10,
                "usage_per_customer": 10,
            }
        }
        _logger.info(f'API Call URL: {url}, Payload: {payload}')
        response = requests.post(url, headers=self.get_header(), data=json.dumps(payload))
        return self.process_response(response)

    def add_coupon_to_cart(self, cart_id, coupon_code):
        """
        Add coupon to the cart
        :param cart_id: Magento Cart ID
        :param coupon_code: Coupon Code
        :return: json - response or None
        """
        url = f'{self.config.host}/rest/all/V1/carts/{cart_id}/coupons/{coupon_code}'
        _logger.info(f'API Call URL: {url}')
        response = requests.put(url, headers=self.get_header())
        return self.process_response(response)

    """
    Helpers
    """
    @staticmethod
    def process_response(res, model=None):
        """
        Helper to validate Magento API response
        :param res: API response
        :param model: Odoo Model
        :return: json response or None
        """
        _logger.info(f"Magento Response: {res.text}")
        if res.ok:
            json_data = json.loads(res.content)
            return json_data
        else:
            msg = f'Magento Integration ERROR: Failed API call. Status code: {res.status_code}\n' \
                f'Reason: {res.text}'
            _logger.error(msg)
            if model:
                model.message_post(subject='Magento Integration ERROR', body=msg, message_type='notification')

    def get_shipping_codes(self, order):
        """
        Get Magento Shipping Codes from Configuration
        :return: shipping_method_code, shipping_carrier_code
        """
        shipping = self.config.mapping_shipping_ids.filtered(lambda r: r.carrier_id.id == order.carrier_id.id)
        if shipping:
            shipping_method_code = shipping[0].mag_shipping_method_code
            shipping_carrier_code = shipping[0].mag_shipping_carrier_code
        else:
            shipping_method_code = self.config.default_shipping_method_code
            shipping_carrier_code = self.config.default_shipping_carrier_code
        return shipping_method_code, shipping_carrier_code
