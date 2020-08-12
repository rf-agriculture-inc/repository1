# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from .connector import MagentoAPI

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model
    def create(self, vals):
        new_id = super(SaleOrderLine, self).create(vals)
        if self.env.company.magento_bridge and new_id.order_id.state in ['sale', 'done']:
            api_connector = MagentoAPI(self)
            if new_id.is_delivery:
                new_id.order_id.mag_update_shipping_price(api_connector)
            else:
                mag_id = api_connector.update_order_item_post(new_id)
                try:
                    new_id.write({'mag_id': mag_id})
                except Exception as e:
                    error_msg = f'{e}. Requested product: {new_id.product_id.display_name}'
                    _logger.error(error_msg)
                    new_id.order_id.message_post(subject='Magento Integration ERROR', body=error_msg, message_type='notification')
        return new_id

    def write(self, vals):
        update_rec = super(SaleOrderLine, self).write(vals)
        if self.env.company.magento_bridge and self.order_id.state in ['sale', 'done'] and not vals.get('mag_id'):
            api_connector = MagentoAPI(self)
            if self.mag_id:
                api_connector.update_order_item(self)
            if self.is_delivery:
                self.order_id.mag_update_shipping_price(api_connector)
        return update_rec

    def unlink(self):
        to_remove_arr = []
        for sol in self:
            to_remove_arr.append({
                'order_id': sol.order_id,
                'mag_id': sol.mag_id,
                'is_delivery': sol.is_delivery,
            })
        res = super(SaleOrderLine, self).unlink()
        if self.env.company.magento_bridge:
            api_connector = MagentoAPI(self)
            for item in to_remove_arr:
                if item['is_delivery']:
                    item['order_id'].mag_update_shipping_price(api_connector)
                if item['mag_id']:
                    api_connector.remove_order_item(item['order_id'], item['mag_id'])
        return res
