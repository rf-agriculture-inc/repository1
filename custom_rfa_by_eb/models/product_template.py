# -*- coding: utf-8 -*-

from odoo import models, fields, api


class RFAProductTemplate(models.Model):
    _inherit = 'product.template'

    purchase_price = fields.Float(compute="_compute_purchase_price", store=True)
    wholesale_markup = fields.Float(related='product_variant_ids.wholesale_markup', readonly=False)

    @api.depends('seller_ids', 'seller_ids.price')
    def _compute_purchase_price(self):
        for record in self:
            si = record.seller_ids
            record.purchase_price = si[0].price if si else 0
