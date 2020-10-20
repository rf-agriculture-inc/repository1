# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from .connector import MagentoAPI

_logger = logging.getLogger(__name__)


class SaleCoupon(models.Model):
    _inherit = 'sale.coupon'

    @api.model
    def create(self, values):
        new_id = super(SaleCoupon, self).create(values)
        if self.env.company.magento_bridge:
            api_connector = MagentoAPI(self)
            res = api_connector.create_sale_rule(new_id.code)
            if res.get('rule_id'):
                api_connector.create_coupon(res.get('rule_id'), new_id.code)
        return new_id
