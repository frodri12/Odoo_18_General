# -*- coding: utf-8 -*-

from odoo import fields, models

class PyResCountry(models.Model):

    _inherit = 'res.country'

    alpha_code = fields.Char(string="Code Alpha 3", size=3, help="Three-letter country codes")
    numeric_code = fields.Char(string="Code Numeric", size=3, help="Three-digit country codes")
