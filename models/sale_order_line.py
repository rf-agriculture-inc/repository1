# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from .connector import MagentoAPI

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def unlink(self):
        order = self.order_id
        mag_id = self.mag_id
        res = super(SaleOrderLine, self).unlink()
        if self.env.company.magento_bridge and mag_id:
            api_connector = MagentoAPI(self)
            api_connector.remove_order_item(order, mag_id)
        return res
