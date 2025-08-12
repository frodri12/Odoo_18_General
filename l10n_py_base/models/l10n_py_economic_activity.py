# -*- coding: utf-8 -*-

from odoo import models, fields

class PyEconomicActivity(models.Model):

    _name = 'l10n_py_economic_activity'
    _description = "Economic activity"
    _rec_name = 'name'
    _order = 'name'

    name = fields.Char(string='Name of economic activity', required=True)
    code = fields.Char(string='Code of economic activity', required=True)

    company_id = fields.Many2one(comodel_name='res.company', string='Company',
        required=True, default=lambda self: self.env.company)
        