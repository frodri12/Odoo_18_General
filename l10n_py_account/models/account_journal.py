# -*- coding: utf-8 -*-

from odoo import fields, models, api, _

import logging

_logger = logging.getLogger(__name__)

class PyAccountJournal(models.Model):

    _inherit = "account.journal"

    l10n_py_is_poe = fields.Boolean(
        compute="_compute_l10n_py_is_poe", store=True, 
        readonly=False, string="It has a expedition point?"
    )
    
    l10n_py_poe_system = fields.Selection(
        selection='_get_l10n_py_poe_system_types_selection', string='Type of Expedition Point',
        compute='_compute_l10n_py_poe_system', store=True, readonly=False
    )
    
    l10n_py_poe_number = fields.Integer(string='Expedition Point')
    
    company_partner = fields.Many2one('res.partner', related='company_id.partner_id')

    #l10n_py_poe_partner_id =fields.Many2one(
    #    'res.partner', 'POE Address',
    #    domain="['|', ('id', '=', company_partner), '&', ('id', 'child_of', company_partner), ('type', '!=', 'contact')]"
    #)
    
    @api.depends('country_code', 'type', 'l10n_latam_use_documents')
    def _compute_l10n_py_is_poe(self):
        for journal in self:
            journal.l10n_py_is_poe = journal.country_code == 'PY' and journal.type == 'sale' and journal.l10n_latam_use_documents
    
    def _get_l10n_py_poe_system_types_selection(self):
        return [
            ('FAP',_('Pre-printed Invoice')), # sale, Facturas, Notas de credito/debito preimpresas o autoimpresion
            ('FAE',_('Electronic Invoice')), # sale, Facturas electronicas
            ('AFP',_('Pre-printed SelfInvoice')), # purchase, Autofacturas
            ('AFE',_('Electronic SelfInvoice')), # purchase, Autofacturas electronicas
            ('REP',_('Pre-printed Delivery Notes')), # sale, Remitos
            ('REE',_('Electronic Delivery Notes')), # sale, Remitos electronicos
            ('FEP',_('Pre-printed Export Invoice')), # sale, Facturas de exportacion
            ('FEE',_('Electronic Export Invoice')), # sale, Facturas de exportacion electronicas
            ('FIP',_('Pre-printed Import Invoice')), # purchase, Facturas de importacion
            ('FIE',_('Electronic Import Invoice')), # purchase, Facturas electronicas de importacion
        ]
        
    @api.depends('l10n_py_is_poe')
    def _compute_l10n_py_poe_system(self):
        for journal in self:
            journal.l10n_py_poe_system = journal.l10n_py_is_poe and journal.l10n_py_poe_system

    ####            

    @api.model
    def _get_codes_per_journal_type(self, poe_system):
        no_pos_docs = ['201','202','203','204','205','206','207','208','209','210','211',
             '102','103','104','105','106','107','108']
        usual_codes = ['109','110','111']
        receipt_codes = ['4']
        afa_codes = ['101']
        codes = []
        if (self.type == 'sale' and not self.l10n_py_is_poe) or (self.type == 'purchase' and poe_system in ['FAP', 'FAE']):
            codes = no_pos_docs
        elif self.type == 'purchase' and poe_system in ('AFP','AFE') :
            # Autofactura
            codes = afa_codes
        elif self.type == 'purchase':
            #_logger.warning("\n\ncode not in " + str(no_pos_docs + afa_codes) + "\n\n")
            return [('code', 'not in', no_pos_docs + afa_codes)]
        elif poe_system in ('FAP','FAE'):
            # pre-printed invoice
            codes = usual_codes + receipt_codes

        #_logger.warning("\n\ncode in " + str(codes) + "\n\n")
        return [('code', 'in', codes)]

    def _get_journal_codes_domain(self):
        self.ensure_one()
        return self._get_codes_per_journal_type(self.l10n_py_poe_system)
