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

