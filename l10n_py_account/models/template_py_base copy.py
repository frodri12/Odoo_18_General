# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, _
from odoo.addons.account.models.chart_template import template


class AccountChartTemplate(models.AbstractModel):
    _inherit = 'account.chart.template'

    @template('py_base')
    def _get_py_base_template_data(self):
        return {
            'property_account_receivable_id': 'base_deudores_por_ventas',
            'property_account_payable_id': 'base_proveedores',
            'property_account_expense_categ_id': 'base_compra_mercaderia',
            'property_account_income_categ_id': 'base_venta_de_mercaderia',
            'name': _('Generic Chart of Accounts Paraguay'),
            'code_digits': '12',
        }

    @template('py_base', 'res.company')
    def _get_py_base_res_company(self):
        return {
            self.env.company.id: {
                'account_fiscal_country_id': 'base.py',
                'bank_account_code_prefix': '1.1.1.02.',
                'cash_account_code_prefix': '1.1.1.01.',
                'transfer_account_code_prefix': '6.0.00.00.',
                'account_default_pos_receivable_account_id': 'base_deudores_por_ventas_pos',
                'income_currency_exchange_account_id': 'base_diferencias_de_cambio',
                'expense_currency_exchange_account_id': 'base_diferencias_de_cambio',
                'account_sale_tax_id': 'vat2',
                'account_purchase_tax_id': 'vat5',

                'account_journal_early_pay_discount_loss_account_id': 'base_diferencias_de_cambio',
                'account_journal_early_pay_discount_gain_account_id': 'base_diferencias_de_cambio',
                'deferred_expense_account_id': 'base_cheques_de_terceros_rechazados',
                'deferred_revenue_account_id': 'base_cheques_diferidos',
            },
        }

    @template('py_base', 'account.journal')
    def _get_py_account_journal(self):
        """ In case of an Paraguay CoA, we modify the default values of the sales journal to be a preprinted journal"""
        return {
            'sale': {
                "name": "Pre-printed sales",
                "code": "0001",
                "l10n_py_dnit_pos_number": 1,
                "l10n_py_dnit_pos_partner_id": self.env.company.partner_id.id,
                "l10n_py_dnit_pos_system": 'II_IM',
                "refund_sequence": True,
            },
        }