# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import _, api, fields, models

class AccountTaxGroup(models.Model):

    _inherit = 'account.tax.group'

    l10n_py_vat_dnit_code = fields.Selection([
        ('0', 'Not Applicable'),
        ('1', 'Untaxed'),
        ('2', 'Exempt'),
        ('3', '0%'),
        ('4', '5%'),
        ('5', '10%'),
    ], string='Tipo de IVA', index=True, readonly=True)
