# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.exceptions import UserError

class PyLatamDocument(models.Model):

    _inherit = "l10n_latam.document.type"

    l10n_avatar_py_edi_code = fields.Integer("EDI Code")
    
    def _format_document_number(self, document_number):
        self.ensure_one()
        if self.country_id.code != "PY":
            return super()._format_document_number(document_number)

        if not document_number:
            return False

        if not self.code:
            return document_number

        # Invoice Number Validator (For Eg: 123-123)
        failed = False
        args = document_number.split('-')
        if len(args) != 3:
            failed = True
        else:
            exp, pos, number = args
            if len(exp) > 3 or not exp.isdigit():
                failed = True
            elif len(pos) > 3 or not pos.isdigit():
                failed = True
            elif len(number) > 7 or not number.isdigit():
                failed = True
            document_number = '{:>03s}-{:>03s}-{:>07s}'.format(exp, pos, number)
        if failed:
            raise UserError(
                _(
                    "%(value)s is not a valid value for %(field)s.\n The following are examples of valid numbers:\n* 1-1-1\n* 001-001-0000001",
                    value=document_number,
                    field=self.name,
                ),
            )

        return document_number    