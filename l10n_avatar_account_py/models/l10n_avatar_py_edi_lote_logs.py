# -*- coding: utf-8 -*-

from odoo import api, fields, models

class PyEdiLoteLogs(models.Model):

    _name = 'l10n_avatar_py_edi_lote_logs'
    _description = 'l10n_avatar_py_edi_lote_logs'

    lote_id = fields.Many2one(
        comodel_name='l10n_avatar_py_edi_lote', string="Lote",
        required=True, readonly=True, index=True
    )
    