# -*- coding: utf-8 -*-

from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    l10n_py_regime_type = fields.Selection(related="company_id.l10n_py_regime_type", 
        string="Regime Type", readonly=False) # related="company_id.regime_type"
