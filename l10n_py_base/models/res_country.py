# -*- coding: utf-8 -*-

from odoo import fields, models

class PyResCountry(models.Model):

    _inherit = 'res.country'

    # Codes for the representation of names of countries and their subdivisions
    l10n_py_alpha_code = fields.Char(string="Code Alpha 3", size=3, help="Three-letter country codes")
    l10n_py_numeric_code = fields.Char(string="Code Numeric", size=3, help="Three-digit country codes")
