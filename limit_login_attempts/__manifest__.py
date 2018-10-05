{
    'name': 'Limit Login Attempts',
    'sequence': 10,
    'author': 'D.Jane',
    'summary': 'Limit login attempts of user.',
    'version': '1.0',
    'description': "",
    'depends': ['web'],
    'data': [
        'views/header.xml',
        'views/config.xml',
        'views/inherit_login.xml',
        'views/templates.xml'
    ],
    'installable': True,
    'application': True,
    'images': ['static/description/banner.jpg'],
    'license': 'OPL-1',
    'currency': 'EUR',
}
