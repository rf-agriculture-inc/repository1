# -*- coding: utf-8 -*-
import logging
import json
from odoo import models, fields, api, _
from .connector import MagentoAPI

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    from_magento = fields.Boolean(default=False, copy=False)

    """
    Overrided Methods
    """
    @api.model
    def create(self, vals):
        if vals.get('from_magento'):
            self.env['sale.order.line.origin'].create(vals)
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

    @api.constrains('product_id')
    def mag_validate_product(self):
        """
        Check if product is enabled in Magento and enable if not
        """
        sku = self.product_id.default_code
        if self.env.company.magento_bridge and sku:
            api_connector = MagentoAPI(self)
            res = api_connector.get_product_by_sku(sku)
            data = json.loads(res.content)
            if res.ok:
                status = data.get('status')
                if status != 1:
                    api_connector.enable_product(self.product_id)
            else:
                msg = data.get('message', False) or data
                _logger.error(msg)

    """
    Custom Logic
    """
    def check_route_required(self):
        """
        Check if route is required on order line
        :return: True if required
        """
        for line in self:
            if line.product_id.type == 'product':
                return True


class SaleOrderLineOrigin(models.Model):
    _name = 'sale.order.line.origin'

    name = fields.Char(string="Description")
    order_id = fields.Many2one('sale.order')
    product_id = fields.Many2one('product.product', string='Product')
    product_uom_qty = fields.Float(string='Quantity', digits='Product Unit of Measure', required=True, default=1.0)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure')
    price_unit = fields.Float('Unit Price', required=True, digits='Product Price', default=0.0)
    tax_id = fields.Many2many('account.tax', string='Taxes')
    discount = fields.Float(string='Discount (%)', digits='Discount', default=0.0)
    mag_quote_id = fields.Integer(string="Magento Quote ID", help="Magento Cart Item ID")
    mag_id = fields.Integer(string="Magento ID", help="Magento Cart Item ID")
    currency_id = fields.Many2one(related='order_id.currency_id', depends=['order_id.currency_id'], store=True,
                                  string='Currency', readonly=True)
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', readonly=True, store=True)
    price_tax = fields.Float(compute='_compute_amount', string='Total Tax', readonly=True, store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', readonly=True, store=True)

    @api.model
    def create(self, vals):
        origin_values = dict()
        for f in self._fields.keys():
            if f in vals.keys():
                origin_values[f] = vals.get(f)
        return super(SaleOrderLineOrigin, self).create(origin_values)

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
                                            product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })
