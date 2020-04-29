# -*- coding: utf-8 -*-
from odoo import models, fields
from .connector import MagentoAPI
from odoo.exceptions import UserError


class ResCompany(models.Model):
    _inherit = 'res.company'

    magento_bridge = fields.Boolean()
    mag_host = fields.Char(string="Host", help="Integration domain")
    mag_consumer_key = fields.Char(string="Consumer Key")
    mag_consumer_secret = fields.Char(string="Consumer Secret")
    mag_access_token = fields.Char(string="Access Token")
    mag_access_token_secret = fields.Char(string="Access Token Secret")


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    magento_bridge = fields.Boolean(related='company_id.magento_bridge', readonly=False)
    mag_host = fields.Char(related='company_id.mag_host', readonly=False)
    mag_consumer_key = fields.Char(related='company_id.mag_consumer_key', readonly=False)
    mag_consumer_secret = fields.Char(related='company_id.mag_consumer_secret', readonly=False)
    mag_access_token = fields.Char(related='company_id.mag_access_token', readonly=False)
    mag_access_token_secret = fields.Char(related='company_id.mag_access_token_secret', readonly=False)

    def test_magento_connection(self):
        """Test call to check connection."""
        try:
            api_connector = MagentoAPI(self)
            res = api_connector.test_connection()
            if res.ok:
                title = "Connection Test Succeeded!"
                message = "Everything seems properly set up!"
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': title,
                        'message': message,
                        'sticky': False,
                    }
                }
            else:
                raise Exception(res.text)
        except Exception as e:
            raise UserError(f"Connection Test Failed! Here is what we got instead:\n{e}")
