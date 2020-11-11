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
            if api_connector.get_config(self).sync_coupons:
                res = api_connector.create_sale_rule(new_id.code)
                if res.get('rule_id'):
                    api_connector.create_coupon(res.get('rule_id'), new_id.code)
        return new_id


class SaleCouponApplyCode(models.TransientModel):
    _inherit = 'sale.coupon.apply.code'

    def apply_coupon(self, order, coupon_code):
        """
        Add coupon to Magento Cart
        """
        res = super(SaleCouponApplyCode, self).apply_coupon(order, coupon_code)
        if self.env.company.magento_bridge and order.mag_quote_id > 0:
            api_connector = MagentoAPI(self)
            if api_connector.get_config(self).sync_coupons:
                api_connector.add_coupon_to_cart(order.mag_quote_id, self.coupon_code)
        return res
