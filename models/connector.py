# -*- coding: utf-8 -*-
import logging
import requests
import json
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


class MagentoAPI:
    """
    Documentation:
    https://devdocs.magento.com/guides/v2.3/get-started/authentication/gs-authentication-token.html
    https://devdocs.magento.com/redoc/2.3/admin-rest-api.html
    """
    def __init__(self, config):
        self.config = config

    def get_header(self):
        if not self.config.mag_access_token:
            raise UserError('Failed to make API call. Access Token is required.')
        return {
            'Authorization': f'Bearer {self.config.mag_access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

    @staticmethod
    def process_response(res):
        if res.ok:
            json_data = json.loads(res.content)
            return json_data
        else:
            msg = f'Failed API call. Status code: {res.status_code}\nReason: {res.text}'
            _logger.error(msg)

    def test_connection(self):
        if not self.config.mag_host:
            raise UserError('Failed to make API call. Host is required.')
        url = f'{self.config.mag_host}/rest/V1/invoices'
        body = {
            "searchCriteria": {
                "filter_groups": []
            }
        }
        return requests.get(url, headers=self.get_header(), params=body)

    def search(self, model, filters):
        url = f'{self.config.mag_host}/rest/V1/{model}/search'
        body = {
            "search_criteria": {
                "filter_groups": [
                    {
                        "filters": filters
                    }
                ]
            }
        }
        response = requests.get(url, headers=self.get_header(), params=body)
        return self.process_response(response)

    def get(self, model, filters):
        url = f'{self.config.mag_host}/rest/V1/{model}'
        body = {
            "search_criteria": {
                "filter_groups": [
                    {
                        "filters": filters
                    }
                ]
            }
        }
        response = requests.get(url, headers=self.get_header(), params=body)
        return self.process_response(response)

    def put(self, model, id, payload):
        url = f'{self.config.mag_host}/rest/V1/{model}/{id}'
        response = requests.put(url, headers=self.get_header(), data=json.dumps(payload))
        return self.process_response(response)

    def post(self, model, payload):
        url = f'{self.config.mag_host}/rest/V1/{model}'
        response = requests.put(url, headers=self.get_header(), data=json.dumps(payload))
        return self.process_response(response)

