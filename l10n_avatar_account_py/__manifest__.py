# -*- coding: utf-8 -*-
{
    'name': "l10n_avatar_account_py",

    'summary': "Facturacion Electronica Paraguay",

    'description': """
El objetivo de este modulo es contar con todos los elementos base
que se requieren para llevar acabo la facturación electrónica en Paraguay
    """,

    'author': "Avatar Informatica SRL",
    'website': "https://www.avatar.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting/Localizations/Account Charts',
    'countries': ['py'],
    'version': '0.5',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'account',
        'l10n_latam_base',
        'l10n_latam_check',
        'l10n_latam_invoice_document',
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'license': 'LGPL-3',
}

