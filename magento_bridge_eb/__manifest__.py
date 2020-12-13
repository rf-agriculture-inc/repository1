# -*- coding: utf-8 -*-
{
    'name': "Magento Bridge EB",

    'summary': """
        Magento Bridge EB""",

    'description': """
        Magento Bridge EB
    """,

    'author': "Dmytro Bartoshchuk",
    'category': 'Uncategorized',
    'version': '1.0',
    'depends': ['base', 'sale', 'sale_management', 'stock', 'account', 'delivery', 'sale_coupon'],
    'data': [
        'security/ir.model.access.csv',
        'data/default_data.xml',
        'data/state_ids.xml',
        'views/config_views.xml',
        'views/custom_views.xml',
        'views/sale_order_views.xml',
        'views/stock_picking_views.xml',
        'views/account_move_views.xml',
        'views/backordered_items.xml',
        'views/sale_order_line_origin_views.xml',
        'views/product_views.xml',
        'views/product_pricelist_views.xml',
        'views/fiscal_position_views.xml',
    ],
}
