# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, _
from odoo.addons.account.models.chart_template import template


class AccountChartTemplate(models.AbstractModel):
    _inherit = 'account.chart.template'

    @template('py_base')
    def _get_py_base_template_data(self):
        return {
            'property_account_receivable_id': 'py_acc_chart_11030101',
            'property_account_payable_id': 'py_acc_chart_21010101',
            'property_account_expense_categ_id': 'py_acc_chart_51010101',
            'property_account_income_categ_id': 'py_acc_chart_41010101',
            'name': _('Generic Chart of Accounts Paraguay'),
            'code_digits': '12',
        }

    @template('py_base', 'res.company')
    def _get_py_base_res_company(self):
        return {
            self.env.company.id: {
                'account_fiscal_country_id': 'base.py',
                'bank_account_code_prefix': '1.1.01.02.',
                'cash_account_code_prefix': '1.1.01.01.',
                'transfer_account_code_prefix': '9.1.01.01.',
                'account_default_pos_receivable_account_id': 'py_acc_chart_11030102',
                'income_currency_exchange_account_id': 'py_acc_chart_42050101',
                'expense_currency_exchange_account_id': 'py_acc_chart_42050101',
                'account_sale_tax_id': 'vat2',
                'account_purchase_tax_id': 'vat5',

                'account_journal_early_pay_discount_loss_account_id': 'py_acc_chart_52990101',
                'account_journal_early_pay_discount_gain_account_id': 'py_acc_chart_42030101',
                'deferred_expense_account_id': 'py_acc_chart_11010204',
                'deferred_revenue_account_id': 'py_acc_chart_21010102',
            },
        }

    @template('py_base', 'account.journal')
    def _get_py_account_journal(self):
        """ In case of an Paraguay CoA, we modify the default values of the sales journal to be a preprinted journal"""
        return {
            'sale': {
                "name": "Facturas preimpresas",
                "code": "0001",
                "l10n_py_dnit_pos_number": 1,
                "l10n_py_dnit_pos_partner_id": self.env.company.partner_id.id,
                "l10n_py_dnit_pos_system": 'II_IM',
                "refund_sequence": True,
            },
        }