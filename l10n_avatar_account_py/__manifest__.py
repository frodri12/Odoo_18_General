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
        'security/ir.model.access.csv',
        
        'data/res.country.csv',
        'data/l10n_latam_identification_type_data.xml',
        'data/res.country.state.csv',
        'data/l10n_avatar_py_municipality.csv',
        #'data/l10n_avatar_py_city.csv',
        'data/l10n_avatar_py_city_data.xml',
        'data/l10n_avatar_py_economic_activity_data.xml',
        'data/uom_data.xml',
        'data/l10n_latam_document_type_data.xml',

        'views/res_country_views.xml',
        'views/res_partner_views.xml',
        'views/res_company:views.xml',
        'views/l10n_avatar_py_municipality_views.xml',
        'views/l10n_avatar_py_city_views.xml',
        'views/l10n_avatar_py_economic_activity_views.xml',
        'views/l10n_avatar_py_economic_activity_company_views.xml',
        'views/uom_uom_views.xml',

        'views/account_journal_views.xml',
        'views/account_tax_views.xml',
        'views/account_tax_group_views.xml',
        'views/account_move_views.xml',
        'views/res_config_settings_views.xml',
        'views/account_payment_view.xml',
        'views/report_invoice.xml',

        'views/menuitem.xml',

        'wizards/account_payment_register_views.xml',
        'reports/l10n_account_py_tax_line_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/py_base_demo.xml'
    ],
    'license': 'LGPL-3',
    'pre_init_hook': '_pre_init_hook',
    'post_init_hook': '_post_init_hook',
}

