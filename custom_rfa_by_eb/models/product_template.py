# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class RFAProductTemplate(models.Model):
    _inherit = 'product.template'

    purchase_price = fields.Float(compute="_compute_purchase_price", store=True)
    wholesale_markup = fields.Float(related='product_variant_ids.wholesale_markup', readonly=False)

    @api.depends('seller_ids', 'seller_ids.price', 'seller_ids.sequence')
    def _compute_purchase_price(self):
        for record in self:
            si = record.seller_ids.sorted(lambda r: r.sequence)
            record.purchase_price = si[0].price if si else 0

    @api.constrains('default_code')
    def validate_sku(self):
        if self.default_code:
            existed = self.search([('active', 'in', [True, False]), ('default_code', '=', self.default_code)])
            if len(existed) > 1:
                raise UserError(f"Product SKU {self.default_code} already exists.")

