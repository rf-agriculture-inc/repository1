# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from .connector import MagentoAPI

_logger = logging.getLogger(__name__)


class SaleCoupon(models.Model):
    _inherit = 'sale.coupon'

    @api.model
    def create(self, values):
        # overridden to automatically invite user to sign up
        new_id = super(SaleCoupon, self).create(values)
        if self.env.company.magento_bridge:
            print(f"Send coupon {new_id.code} to Magento")
            api_connector = MagentoAPI(self)
            res = api_connector.create_sale_rule(new_id.code)
            if res.get('rule_id'):
                api_connector.generate_coupon(res.get('rule_id'), new_id.code)
        return new_id
