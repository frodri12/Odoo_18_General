# -*- coding: utf-8 -*-

from odoo import models, api, fields, _
from odoo.exceptions import UserError

class PyL10nLatamDocumentType(models.Model):

    _inherit = 'l10n_latam.document.type'

    def _format_document_number(self, document_number):
        self.ensure_one()
        if self.country_id.code != "PY":
            return super()._format_document_number(document_number)

        if not document_number:
            return False

        if not self.code:
            return document_number

        if self.code in ['102','103','104','105','106','107','108']:
            return document_number

        if self.code in ['201','202','203','204','205','206','207','208','209','210','211']:
            return document_number

        # Invoice Number Validator (For Eg: 123-123-1234567)
        failed = False
        args = document_number.split('-')
        if len(args) != 3:
            failed = True
        else:
            organization, expedition, number = args
            if len(organization) > 3 or not organization.isdigit():
                failed = True
            elif len(expedition) > 3 or not expedition.isdigit():
                failed = True
            elif len(number) > 7 or not number.isdigit():
                failed = True
            document_number = '{:>03s}-{:>03s}-{:>07s}'.format(organization, expedition, number)
        if failed:
            raise UserError(
                _(
                    "%(value)s is not a valid value for %(field)s.\nThe document number must be entered with a dash (-) and a maximum of 3 characters for the first part, 3 character for the second part and 7 for the third.",
                    value=document_number,
                    field=self.name
                )
            )
        return document_number