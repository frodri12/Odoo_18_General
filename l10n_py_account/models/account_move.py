# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.osv import expression
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import logging


_logger = logging.getLogger(__name__)

class AccountMove(models.Model):

    _inherit = 'account.move'

    def _get_formatted_sequence(self, number=0):
        return "%s %03d-%03d-%07d" % (self.l10n_latam_document_type_id.doc_code_prefix,
                                 self.company_id.l10n_py_organization_number,
                                 self.journal_id.l10n_py_poe_number, number)

    def _get_starting_sequence(self):
        if self.journal_id.l10n_latam_use_documents and self.company_id.account_fiscal_country_id.code == "PY":
            if self.l10n_latam_document_type_id:
                return self._get_formatted_sequence()
        return super()._get_starting_sequence()

    def _is_manual_document_number(self):
        if self.country_code != 'PY':
            return super()._is_manual_document_number()
        return self.l10n_latam_use_documents and self.journal_id.type in ['purchase', 'sale'] and \
            not self.journal_id.l10n_py_is_poe

    @api.constrains('move_type', 'journal_id')
    def _check_moves_use_documents(self):
        """ Do not let to create not invoices entries in journals that use documents """
        not_invoices = self.filtered(lambda x: x.company_id.account_fiscal_country_id.code == "PY" and x.journal_id.type in ['sale', 'purchase'] and x.l10n_latam_use_documents and not x.is_invoice())
        if not_invoices:
            raise ValidationError(_("The selected Journal can't be used in this transaction, please select one that doesn't use documents as these are just for Invoices."))

    ####
        
    @api.depends('l10n_latam_available_document_type_ids')
    def _compute_l10n_latam_document_type(self):
        for rec in self.filtered(lambda x: x.state == 'draft' and (not x.posted_before if x.move_type in ['out_invoice', 'out_refund'] else True)):
            document_types = rec.l10n_latam_available_document_type_ids._origin
            rec.l10n_latam_document_type_id = document_types and document_types[0].id

    @api.model
    def _get_l10n_py_codes_used_for_inv_and_ref(self):
        return ['110','209','210']     

    def _get_l10n_latam_documents_domain(self):
        self.ensure_one()
        domain = super()._get_l10n_latam_documents_domain()
        if self.journal_id.company_id.account_fiscal_country_id.code == "PY":
            domain = expression.AND([
                domain or [],
                self.journal_id._get_journal_codes_domain(),
            ])
            if self.move_type in ['out_refund', 'in_refund']:
                domain = ['|', ('code', 'in', self._get_l10n_py_codes_used_for_inv_and_ref())] + domain
        return domain

    @api.constrains('move_type', 'l10n_latam_document_type_id')
    def _check_invoice_type_document_type(self):
        docs_used_for_inv_and_ref = self.filtered(
            lambda x: x.country_code == 'PY' and
            x.l10n_latam_document_type_id.code in self._get_l10n_py_codes_used_for_inv_and_ref() and
            x.move_type in ['out_refund', 'in_refund'])

        super(AccountMove, self - docs_used_for_inv_and_ref)._check_invoice_type_document_type()

    @api.onchange('l10n_latam_document_type_id', 'l10n_latam_document_number', 'partner_id')
    def _inverse_l10n_latam_document_number(self):
        super()._inverse_l10n_latam_document_number()

        to_review = self.filtered(lambda x: (
            x.journal_id.l10n_py_is_poe
            and x.l10n_latam_document_type_id
            and x.l10n_latam_document_number
            and (x.l10n_latam_manual_document_number or not x.highest_name)
            and x.l10n_latam_document_type_id.country_id.code == 'PY'
        ))
        for rec in to_review:
            number = rec.l10n_latam_document_type_id._format_document_number(rec.l10n_latam_document_number)
            current_poe = int(number.split("-")[1])
            current_exp = int(number.split("-")[0])
            if current_poe != rec.journal_id.l10n_py_poe_number or current_exp != rec.company_id.l10n_py_organization_number:
                invoices = self.search([('journal_id', '=', rec.journal_id.id), ('posted_before', '=', True)], limit=1)
                # If there is no posted before invoices the user can change the POE number (x.l10n_latam_document_number)
                if (not invoices):
                    rec.journal_id.l10n_py_poe_number = current_poe
                    #rec.journal_id._onchange_set_short_name()
                # If not, avoid that the user change the POS number
                else:
                    raise UserError(_('The document number can not be changed for this journal, you can only modify'
                                      ' the POE number if there is not posted (or posted before) invoices'))
