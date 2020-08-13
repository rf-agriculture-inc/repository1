{
    'name': 'RFP HR Attendance',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'version': '1.0.0.0.0',
    'category': 'Sale',
    'description': """
Red Flag Products HR Attendance Customizations
    """,
    'website': 'https://hibou.io/',
    'depends': [
        'hr',
        'hr_attendance',
    ],
    'data': [
        'views/hr_views.xml',
        'views/web_assets.xml',
    ],
    'qweb': [
        'static/src/xml/hr_attendance.xml',
    ],
    'installable': True,
    'application': False,
}
