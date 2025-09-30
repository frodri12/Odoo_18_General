# -*- coding: utf-8 -*-

from odoo import fields, models

class PyCity(models.Model):

    _name = "l10n_avatar_py_city"
    _description = "l10n_avatar_py_city"

    name = fields.Char()
    code = fields.Char()
    comments = fields.Text()

    municipality_id = fields.Many2one(comodel_name='l10n_avatar_py_municipality', string="Municipio")
    state_id = fields.Many2one(comodel_name='res.country.state',string="Estado")
    country_id = fields.Many2one(comodel_name='res.country')

    date_from = fields.Date(string="Valido desde")

    is_editable_for_group = fields.Boolean(compute='_compute_is_editable_for_group')

    def _compute_is_editable_for_group(self):
        for record in self:
            record.is_editable_for_group = self.env.user.has_group('base.group_system')
