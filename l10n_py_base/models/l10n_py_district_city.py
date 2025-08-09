# -*- coding: utf-8 -*-

from odoo import models, fields

class PyDistrictCity(models.Model):

    _name = "l10n_py_district_city"
    _description = "l10n_py_district_city"

    name = fields.Char()
    code = fields.Integer()

    district_id = fields.Many2one("l10n_py_state_district")
    country_id = fields.Many2one("res.country")

    is_editable_for_group = fields.Boolean(compute='_compute_is_editable_for_group')

    def _compute_is_editable_for_group(self):
        for record in self:
            record.is_editable_for_group = self.env.user.has_group('base.group_system')
