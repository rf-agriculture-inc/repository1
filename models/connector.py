# -*- coding: utf-8 -*-
import logging
import requests
import json
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

    # def get(self, model, filters):
    #     url = f'{self.config.host}/rest/V1/{model}'
    #     body = {
    #         "search_criteria": {
    #             "filter_groups": [
    #                 {
    #                     "filters": filters
    #                 }
    #             ]
    #         }
    #     }
    #     response = requests.get(url, headers=self.get_header(), params=body)
    #     return self.process_response(response)

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
                "quote_id": quote_id
            }
        }
        response = requests.post(url, headers=self.get_header(), data=json.dumps(payload))
        return self.process_response(response, line.order_id)

    def add_ship_bill_info(self, quote_id, order):
        """
        Add shipping and billing info
        :param quote_id: Magento Quotation ID
        :param order: Odoo Sale Order
        :return: json - response or None
        """
        url = f'{self.config.host}/rest/V1/carts/{quote_id}/shipping-information'
        _logger.info(f'API Call URL: {url}')

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
                    "region_id": 1,  # TODO: Check what is region_id in Magento
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
                    "region_id": 1,  # TODO: Check what is region_id in Magento
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
        payment_method = self.config.default_payment_method  # TODO: payment method mapping
        method_code, carrier_code = self.get_shipping_codes(order)
        payload = {
            "paymentMethod": {
                "method": payment_method
            },
            "shippingMethod": {
                "method_code": method_code,
                "carrier_code": carrier_code,
                "additionalProperties": {}
            }
        }
        response = requests.put(url, headers=self.get_header(), data=json.dumps(payload))
        return self.process_response(response, order)

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
        _logger.debug(f"Magento Response: {res.text}")
        if res.ok:
            json_data = json.loads(res.content)
            return json_data
        else:
            msg = f'Magento Integration ERROR: Failed API call. Status code: {res.status_code}\n' \
                f'Reason: {res.text}'
            _logger.error(msg)
            if model:
                model.message_post(subject='Magento Integration ERROR', body=msg, message_type='notification')

    # def get_payment_method(self, order):
    #     """
    #     Get Magento Payment Method from Configuration
    #     :return: str, payment method
    #     """
    #     payment = self.config.mapping_payment_ids.filtered(lambda r: r.journal_id.id == order.journal_id.id)
    #     if payment:
    #         payment_method = payment[0].mag_payment_method
    #     else:
    #         payment_method = self.config.default_payment_method
    #     return payment_method

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
