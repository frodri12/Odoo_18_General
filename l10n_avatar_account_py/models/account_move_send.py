# -*- coding: utf-8 -*-

from odoo import _, api, models
from odoo.addons.account.models.account_move import AccountMove

class PyAccountMoveSend(models.AbstractModel):

    _inherit = "account.move.send"


    @api.model
    def _get_placeholder_mail_attachments_data(self, move, invoice_edi_format=None, extra_edis=None):
        if move.invoice_pdf_report_id:
            return []

        if move.journal_id.l10n_avatar_py_poe_system not in ('FAE','AFE'):
            return super()._get_placeholder_mail_attachments_data(move, invoice_edi_format, extra_edis)

        filename = move._get_invoice_report_filename()
        filenameXML = move._get_invoice_report_filename(extension='xml')
        return [{
            'id': f'placeholder_{filename}',
            'name': filename,
            'mimetype': 'application/pdf',
            'placeholder': True,
        },{
            'id': f'placeholder_{filenameXML}',
            'name': filenameXML,
            'mimetype': 'application/xml',
            'placeholder': True,
        }]

    def _get_invoice_extra_attachments(self, move):
        # EXTENDS 'account'
        if move.journal_id.l10n_avatar_py_poe_system in ('FAE','AFE'):
            return super()._get_invoice_extra_attachments(move) + move.invoice_xml_report_id
        return super()._get_invoice_extra_attachments(move)

