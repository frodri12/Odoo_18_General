# -*- coding: utf-8 -*-
from odoo import api, fields, models

class L10npyRegimeType(models.Model):
    _name = "l10n_py.regime.type"
    _description = "L10n PY Regime Type"

    code = fields.Integer(string="Code", required=True)
    name = fields.Char(string="Name", required=True)
    active = fields.Boolean(string="Active", default=True)