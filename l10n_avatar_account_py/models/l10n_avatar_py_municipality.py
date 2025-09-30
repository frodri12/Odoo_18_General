# -*- coding: utf-8 -*-

from odoo import fields, models

class PyMunicipality(models.Model):

    _name = "l10n_avatar_py_municipality"
    _description = "l10n_avatar_py_municipality"

    name = fields.Char()
    code = fields.Char()
    comments = fields.Text()
    country_id = fields.Many2one('res.country')

    date_from = fields.Date(string="Valido desde")
    state_id = fields.Many2one('res.country.state',string="Estado")


    city_ids = fields.One2many(comodel_name='l10n_avatar_py_city', inverse_name='municipality_id', string='Ciudades')

    is_editable_for_group = fields.Boolean(compute='_compute_is_editable_for_group')

    def _compute_is_editable_for_group(self):
        for record in self:
            record.is_editable_for_group = self.env.user.has_group('base.group_system')

    