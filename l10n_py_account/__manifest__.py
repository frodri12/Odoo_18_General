# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "Paraguay - Accounting",
    'website': "https://www.avatar.com.py",
    'icon': '/account/static/description/l10n.png',
    'countries': ['py'],
    'version': '0.6',
    'author': "Avatar Informatica SRL",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/18.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting/Localizations/Account Charts',
    'description': """
General Chart of Accounts.
==========================

This module adds accounting functionalities for the Paraguayan localization, representing the minimum required configuration for a company to operate in Paraguay under the regulations and guidelines provided by the DNIT (Dirección Nacional de Ingresos Tributarios).

Among the functionalities are:

* Paraguayan Generic Chart of Account
* Pre-configured VAT Taxes and Tax Groups.
* Legal document types in Paraguay.
* Valid contact identification types in Paraguay.
* Configuration and activation of Paraguayan Currencies  (PYG).
* Frequently used default contacts already configured: DNIT, Consumidor Final Paraguayo.

Configuration
-------------

Demo data for testing:

* Paraguayan company named "PY Company" with the Paraguayan chart of accounts already installed, pre configured taxes, document types and identification types.
* Paraguayan contacts for testing:

   * IEB Internacional
   * Consumidor Final Anónimo Uruguayo.

       """,
    # any module necessary for this one to work correctly
    'depends': [
        'l10n_latam_invoice_document',
        'l10n_latam_base',
        'account',
    ],
    # always loaded
    'data': [
        'security/ir.model.access.csv',

        'data/res_user_data.xml',
        'data/res_partner_data.xml',
        'data/l10n_latam_identification_type_data.xml',
        'data/l10n_py_dnit_responsibility_type_data.xml',
        'data/uom_uom_data.xml',
        'data/l10n_latam.document.type.csv',
        'data/res.country.csv',
        'data/res_country_state_data.xml',
        'data/l10n_py_district_data.xml',
        'data/l10n_py_city_data.xml',
        'data/l10n_py_regime_type_data.xml',

        'views/dnit_menuitem.xml',
        'views/l10n_py_dnit_responsibility_type_view.xml',
        'views/l10n_latam_document_type_view.xml',
        'views/account_journal_view.xml',
        'views/res_partner_view.xml',
        'views/res_company_view.xml',
        'views/res_country_view.xml',
        'views/uom_uom_view.xml',
        'views/res_config_settings_view.xml',
        'views/account_move_view.xml',
        'views/l10n_py_economic_activity_view.xml',
        'views/report_invoice.xml',
        'views/account_tax_view.xml',
        'views/product_template_view.xml',
        'views/account_report.xml',
        'views/report_payment_receipt_templates.xml',
        'views/report_payment_order_templates.xml',
        'report/account_py_vat_line_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/py_base_demo.xml',
        'demo/res_partner_demo.xml',
        'demo/product_product_demo.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
    'pre_init_hook': '_set_change_values',
}
