# -*- coding: utf-8 -*-
from odoo import fields, models

class PyUom(models.Model):

    _inherit = 'uom.uom'

    l10n_py_code = fields.Integer('Internal Code', help='Paraguay: This code will be used on electronic invoice.')
    l10n_py_ref = fields.Char('Internal Reference', help='Paraguay: This name will be used on electronic invoice.')
    l10n_py_description = fields.Char('Description')
    