# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "Paraguayan Electronic Invoicing",
    'website': "https://www.avatar.com.py",
    'icon': '/account/static/description/l10n.png',
    'countries': ['py'],
    'version': '0.6',
    'author': "Avatar Informatica SRL",
    'category': 'Accounting/Localizations/EDI',

    # any module necessary for this one to work correctly
    'depends': ['l10n_py_account'],
    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data/ir_config_parameter_data.xml',
        'views/res_config_settings_view.xml',
        'views/account_move_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        #'demo/demo.xml',
    ],
    'installable': True,
    'auto_install': ['l10n_py_account'],
    'license': 'LGPL-3',
    'assets': {
        'web._assets_core': [
            ('replace', 'web/static/src/core/notifications/notification.xml', 'l10n_py_account_edi/static/src/core/notifications/notification.xml'),
            ('replace', 'web/static/src/core/notifications/notification.scss', 'l10n_py_account_edi/static/src/core/notifications/notification.scss'),
            ('replace', 'web/static/src/core/notifications/notification.variables.scss', 'l10n_py_account_edi/static/src/core/notifications/notification.variables.scss'),
        ],
    }
}

