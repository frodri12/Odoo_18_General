# -*- coding: utf-8 -*-
{
    'name': "Paraguay Localization Base",

    'summary': "Paraguay Localization Base",

    'description': """
Long description of module's purpose
    """,

    'author': "Avatar Informatica SRL",
    'website': "https://www.avatar.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    # Accounting/Localization/Account Charts
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'contacts',
        'account',
        'l10n_latam_base',
        'l10n_latam_invoice_document',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        
        'data/res.country.csv',
        'data/res_country_state_data.xml',
        'data/l10n_py_state_district_data.xml',
        'data/l10n_py_district_city_data.xml',
        'data/uom_data.xml',
        'data/l10n_latam_identification_type_data.xml',

        'views/views.xml',
        'views/templates.xml',
        'views/res_country_views.xml',
        'views/l10n_py_state_district_views.xml',
        'views/l10n_py_district_city_views.xml',
        'views/res_partner_views.xml',
        'views/res_company_views.xml',
        'views/uom_uom_views.xml',
        'views/res_config_settings_views.xml',
        
        'views/menuitem.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'license': 'LGPL-3',
    'pre_init_hook': '_pre_change_values',
    'post_init_hook': '_post_change_values',
}

