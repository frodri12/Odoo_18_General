# -*- coding: utf-8 -*-

from odoo import _, api, fields, models

class PyAccountTaxGroup(models.Model):

    _inherit = 'account.tax.group'

    l10n_avatar_py_tax_type = fields.Selection([
        ('0','Exento'),
        ('5','5%'),
        ('10','10%'),
    ], default="10", string="Tasa del IVA")