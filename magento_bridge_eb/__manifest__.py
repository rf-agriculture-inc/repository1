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
    'depends': ['base', 'sale', 'sale_management', 'stock', 'account', 'delivery'],
    'data': [
        'security/ir.model.access.csv',
        'data/default_data.xml',
        'views/config_views.xml',
        'views/custom_views.xml',
        'views/sale_order_views.xml',
        'views/stock_picking_views.xml',
        'views/account_move_views.xml',
    ],
}