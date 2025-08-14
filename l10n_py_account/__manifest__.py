# -*- coding: utf-8 -*-
{
    'name': "l10n_py_account",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "Avatar Informatica SRL",
    'website': "https://www.avatar.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'countries': ['py'],
    'category': 'Accounting/Localizations/Account Charts',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','l10n_py_base'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        
        'views/account_tax_group_views.xml',
        'views/account_tax_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'license': 'LGPL-3',
}

