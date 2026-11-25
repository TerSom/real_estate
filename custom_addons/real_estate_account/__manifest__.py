{
    'name': 'Real Estate Account',
    'version': '20.0.1.0.0',
    'category': 'Services',
    'summary': 'Real Estate Management System Account',
    'description': """Real Estate Management System Account""",
    'author': 'Tersom',
    'depends': ['real_estate', 'account'],
    'data': [
        'views/real_estate_property_views.xml',
        'views/account_move_views.xml',
    ],
    'assets': {
    'web.assets_backend': [
        ],
    },
    'installable': True,
    'auto_install': True,
    'application': False,
    'license': 'LGPL-3',
}
