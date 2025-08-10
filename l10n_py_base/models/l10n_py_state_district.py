# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PyStateDistrict(models.Model):

    _name = "l10n_py_state_district"
    _description = "Paraguay - Districts"
    _order = 'name'
    _rec_names_search = ['name', 'code']

    state_id = fields.Many2one(comodel_name="res.country.state",string="Department", required=True)
    name = fields.Char(string="District Name", required=True)
    code = fields.Integer(string="District Code", required=True)

    city_ids = fields.One2many(comodel_name='l10n_py_district_city', inverse_name='district_id', string='Cities')
    country_id = fields.Many2one(comodel_name="res.country",string="Country")

    _sql_constraints = [
        ('code_uniq', 'unique (code)',
            'The code of the district must be unique!')
    ]

    is_editable_for_group = fields.Boolean(compute='_compute_is_editable_for_group')

    def _compute_is_editable_for_group(self):
        for record in self:
            record.is_editable_for_group = self.env.user.has_group('base.group_system')
