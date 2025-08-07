# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

class ResCountry(models.Model):

    _inherit = 'res.country'

    l10n_py_alpha_code = fields.Char(
        'Alpha3 Code', size=3, help='Este código se utilizará en la factura electrónica.')
    l10n_py_alpha_number = fields.Char(
        'ISO Number'
    )
    