{
    'name': 'RFP HR Attendance',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'version': '13.0.1.0.0',
    'category': 'Sale',
    'description': """
Red Flag Products HR Attendance Customizations
    """,
    'website': 'https://hibou.io/',
    'depends': [
        'hr_payroll_attendance', # Used for default work type ATTN
    ],
    'data': [
        'data/work_type_data.xml',
        'views/hr_views.xml',
        'views/web_assets.xml',
    ],
    'qweb': [
        'static/src/xml/hr_attendance.xml',
    ],
    'installable': True,
    'application': False,
}
