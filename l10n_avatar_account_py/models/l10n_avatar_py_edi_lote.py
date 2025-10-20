# -*- coding: utf-8 -*-

from odoo import api, fields, models

class PyEdiLote(models.Model):

    _name = 'l10n_avatar_py_edi_lote'
    _description = 'l10n_avatar_py_edi_lote'

    move_id = fields.Many2one(
        comodel_name='account.move', string="Documento",
        required=True, readonly=True, index=True
    )
    
    name = fields.Char( related="move_id.l10n_latam_document_number", readonly=True)
    lote_number = fields.Char(string="Numero de lote")

    log_id = fields.One2many(
        'l10n_avatar_py_edi_lote_logs', 'lote_id', string="Documento",
        copy=False
    )

    request_json = fields.Text( readonly=True)
    response_json = fields.Text( readonly=True)

    request_date = fields.Datetime(readonly=True)
    response_date = fields.Datetime(readonly=True)
    resenvilotede_dcodres = fields.Char(readonly=True)
    resenvilotede_dmsgres = fields.Char(readonly=True)
    resenvilotede_dprotconslote = fields.Char(readonly=True)
    resenvilotede_dtpoproces = fields.Char(readonly=True)
    resenvilotede_res_id = fields.Integer(readonly=True)
    resenvilotede_res_qr = fields.Char(readonly=True)
    resenvilotede_res_cdc = fields.Char(readonly=True)

    resenviconslotede_dcodreslot = fields.Char(readonly=True)
    resenviconslotede_dmsgreslot = fields.Char(readonly=True)
    resenviconslotede_id = fields.Char(readonly=True)
    resenviconslotede_destrec = fields.Char(readonly=True)
    resenviconslotede_dprotaut = fields.Char(readonly=True)
    resenviconslotede_dcodres = fields.Char(readonly=True)
    resenviconslotede_dmsgres = fields.Char(readonly=True)
    


