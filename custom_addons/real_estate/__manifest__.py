{
    'name': 'Real Estate',
    'version': '1.0',
    'category': 'Services',
    'summary': 'Real Estate Management System',
    'description': """Real Estate Management System""",
    'author': 'Tersom',
    'depends': ['base','mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/real_estate_property.xml',
        'views/real_estate_tag.xml',
        'views/real_estate_type.xml',
        'views/real_estate_menu.xml',
    ],
    'assets': {
    'web.assets_backend': [
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
