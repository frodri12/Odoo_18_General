# -*- coding: utf-8 -*-

from odoo import fields, models

class PyAccountTax(models.Model):

    _inherit = "account.tax"

    l10n_py_tax_base_percent = fields.Float(string="Tax base percent", default = 100.0)
    