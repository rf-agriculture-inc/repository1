# -*- coding: utf-8 -*-
{
    'name': "Magento Bridge EB",

    'summary': """
        Magento Bridge EB""",

    'description': """
        Magento Bridge EB
    """,

    'author': "Dm Bart",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'sale', 'sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'data/default_data.xml',
        'views/config_views.xml',
        'views/custom_views.xml',
        'views/sale_order_views.xml',
    ],
}
