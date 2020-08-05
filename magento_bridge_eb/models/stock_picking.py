# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from .connector import MagentoAPI

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    mag_id = fields.Integer(string="Magento Shipment ID", readonly=True, copy=False)

    def action_done(self):
        """Send Shipped Items to Magento"""
        res = super(StockPicking, self).action_done()
        if self.env.company.magento_bridge and self.carrier_tracking_ref:
            self.mag_send_shipment()
        return res

    def mag_send_shipment(self):
        """Create Shipment in Magento"""
        if self.sale_id and self.sale_id.mag_id:
            api_connector = MagentoAPI(self)
            res = api_connector.create_shipment(self)
            if res:
                try:
                    mag_shipment_id = int(res)
                    self.mag_id = mag_shipment_id
                    msg = f'Shipment sent to Magento. Magento Order ID: {mag_shipment_id}'
                    self.message_post(subject='Magento Integration Success', body=msg, message_type='notification')
                except Exception as e:
                    _logger.error(e)


