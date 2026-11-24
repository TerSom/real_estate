{
    'name': 'Real Estate',
    'version': '20.0.1.0.0',
    'category': 'Services',
    'summary': 'Real Estate Management System Account',
    'description': """Real Estate Management System Account""",
    'author': 'Tersom',
    'depends': ['real_estate', 'account'],
    'data': [
        'views/real_estate_property.xml'
    ],
    'assets': {
    'web.assets_backend': [
        ],
    },
    'installable': True,
    'auto_install': True,
    'application': True,
    'license': 'LGPL-3',
}
