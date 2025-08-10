# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.osv import expression

class PyDistrictCity(models.Model):

    _name = "l10n_py_district_city"
    _description = "Paraguay - Cities"

    district_id = fields.Many2one(comodel_name="l10n_py_state_district", string="District", required=True)
    name = fields.Char(string="City Name", required=True)
    code = fields.Integer(string="City Code", required=True)

    country_id = fields.Many2one("res.country")

    _sql_constraints = [
        ('code_uniq', 'unique (code)',
            'The code of the city must be unique!')
    ]

    is_editable_for_group = fields.Boolean(compute='_compute_is_editable_for_group')

    def _compute_is_editable_for_group(self):
        for record in self:
            record.is_editable_for_group = self.env.user.has_group('base.group_system')

