# -*- coding: utf-8 -*-
from odoo import fields, models

class PyAccountTaxGroup(models.Model):

    _inherit = 'account.tax.group'

    l10n_py_tax_type = fields.Selection([
        ('tax_10','TAX 10%'),('tax_5','TAX 5%'),('tax_0','TAX 0%'),
        ('perception','Perception'),('retention','Retention')
    ], string='Tax types')

    