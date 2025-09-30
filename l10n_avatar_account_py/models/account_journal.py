# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)

class PyAccountJournal(models.Model):

    _inherit = "account.journal"

    l10n_avatar_py_poe_system = fields.Selection(
        selection='_get_l10n_avatar_py_poe_types_selection', string='Tipos de documentos',
        compute='_compute_l10n_avatar_py_poe_system', store=True, readonly=False,
    )

    l10n_avatar_py_branch = fields.Integer(string="Establecimiento", default=1)
    l10n_avatar_py_dispatch_point = fields.Integer(string="Punto de Expedición", default=1)

    l10n_avatar_py_address_id = fields.Many2one(
        comodel_name='res.partner', string="Dirección del Establecimiento", 
        domain="['|', ('id', '=', company_partner_id), '&', ('id', 'child_of', company_partner_id), ('type', '!=', 'contact')]"
        )

    # Timbrado
    l10n_avatar_py_authorization_code = fields.Char(string="Timbrado")
    l10n_avatar_py_authorization_startdate = fields.Date(string="Fecha inicio de Timbrado")
    l10n_avatar_py_authorization_enddate = fields.Date(string="Fecha de fin de Timbrado")
    l10n_avatar_py_authorization_number = fields.Char(string="Número de autorizacion del Timbrado")

    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if res.get('company_id') != None and res.get('l10n_avatar_py_address_id') == None:
            partner_id = self.env.company.partner_id.id
            res['l10n_avatar_py_address_id'] = partner_id
        return res

    def _get_l10n_avatar_py_poe_types_selection(self):
        return [
            ('FAP',_('Pre-printed Invoice')), # sale/purchase, Facturas, Notas de credito/debito preimpresas o autoimpresion
            ('FAE',_('Electronic Invoice')), # sale/purchase, Facturas electronicas
            ('AFP',_('Pre-printed SelfInvoice')), # purchase, Autofacturas
            ('AFE',_('Electronic SelfInvoice')), # purchase, Autofacturas electronicas
            ('REP',_('Pre-printed Delivery Notes')), # sale/purchase, Remitos
            ('REE',_('Electronic Delivery Notes')), # sale/purchase, Remitos electronicos
            ('FEP',_('Pre-printed Export Invoice')), # sale, Facturas de exportacion (a futuro)
            ('FEE',_('Electronic Export Invoice')), # sale, Facturas de exportacion electronicas (a futuro)
            ('FIP',_('Pre-printed Import Invoice')), # purchase, Facturas de importacion (a futuro)
            ('FIE',_('Electronic Import Invoice')), # purchase, Facturas electronicas de importacion (a futuro)
        ]

    @api.depends('l10n_latam_use_documents')
    def _compute_l10n_avatar_py_poe_system(self):
        for journal in self:
            journal.l10n_avatar_py_poe_system = journal.l10n_latam_use_documents and journal.l10n_avatar_py_poe_system

    def _get_journal_codes_domain(self):
        self.ensure_one()
        return self._get_codes_per_journal_type(self.l10n_latam_use_documents, self.l10n_avatar_py_poe_system)

    @api.model
    def _get_codes_per_journal_type(self, latam_use_documents, py_poe_system):
        codes = []
        usual_codes = ['109','110','111','112']
        autofactura = ['101']
        #
        if self.type == 'sale':
            if latam_use_documents:
                codes = usual_codes
        elif self.type == 'purchase':
            if latam_use_documents and py_poe_system in ('AFP','AFE'):
                codes = autofactura
            if latam_use_documents and (not py_poe_system or py_poe_system not in ('AFP','AFE')):
                codes = usual_codes
        return [('code', 'in', codes)]

    @api.constrains('l10n_avatar_py_branch')
    def _check_l10n_avatar_py_branch(self):
        journals = self.filtered(lambda j: j.l10n_latam_use_documents)
        for journal in journals:
            if journal.type == 'sale':
                if journal.l10n_avatar_py_branch == 0:
                    raise ValidationError('El valor del establecimiento no puede ser cero')
                elif journal.l10n_avatar_py_branch > 999:
                    raise ValidationError('El valor del establecimiento is inválido (Max 3 digitos)')
            elif journal.type == 'purchase' and journal.l10n_avatar_py_poe_system and journal.l10n_avatar_py_poe_system in ('AFP','AFE'):
                if journal.l10n_avatar_py_branch == 0:
                    raise ValidationError('El valor del establecimiento no puede ser cero')
                elif journal.l10n_avatar_py_branch > 999:
                    raise ValidationError('El valor del establecimiento is inválido (Max 3 digitos)')


    @api.constrains('l10n_avatar_py_dispatch_point')
    def _check_l10n_avatar_py_dispatch_point(self):
        journals = self.filtered(lambda j: j.l10n_latam_use_documents)
        for journal in journals:
            if journal.type == 'sale':
                if journal.l10n_avatar_py_dispatch_point == 0:
                    raise ValidationError('El valor del punto de expedición no puede ser cero')
                elif journal.l10n_avatar_py_dispatch_point > 999:
                    raise ValidationError('El valor del punto de expedición is inválido (Max 3 digitos)')
            elif journal.type == 'purchase' and journal.l10n_avatar_py_poe_system and journal.l10n_avatar_py_poe_system in ('AFP','AFE'):
                if journal.l10n_avatar_py_dispatch_point == 0:
                    raise ValidationError('El valor del punto de expedición no puede ser cero')
                elif journal.l10n_avatar_py_dispatch_point > 999:
                    raise ValidationError('El valor del punto de expedición is inválido (Max 3 digitos)')

    def _get_xmlgen_Establecimiento( self):
        est = {}
        est.update( { 'codigo': "001"})
        addressId = self.l10n_avatar_py_address_id
        if not addressId:
            raise ValidationError("No se definio la direccion en el diario %s" % self.name)
        direccion = addressId.street
        numeroCasa = addressId.external_number
        complementoDireccion1 = addressId.street2
        departamento = addressId.state_id.code
        distrito = addressId.municipality_id.code
        ciudad = addressId.city_id.code
        telefono = addressId.phone
        email = addressId.email
        denominacion = addressId.name
        if not direccion:
            raise ValidationError("No se definio la calle en el contacto de la compania")
        est.update( { 'direccion': direccion}) #D107
        if numeroCasa:
            est.update( { 'numeroCasa': numeroCasa}) #D108
        else:
            est.update( { 'numeroCasa': 0})
        if complementoDireccion1:
            est.update( { 'complementoDireccion1': complementoDireccion1}) #D109
        if departamento:
            est.update( { 'departamento': int(departamento)}) #D111
        else:
            raise ValidationError("No se definio el departamento del contacto de la compania")
        if distrito:
            est.update( { 'distrito': int(distrito)}) #D113
        #else:
        #    raise ValidationError("No se definio el municipio del contacto de la compania")
        if ciudad:
            est.update( { 'ciudad': int(ciudad)}) #D115
        else:
            raise ValidationError("No se definio la ciudad del contacto de la compania")
        if telefono:
            est.update( { 'telefono': telefono}) #D117
        else:
            raise ValidationError("No se definio el telefono en el contacto de la compania")
        if email:
            est.update( { 'email': email}) #D118
        else:
            raise ValidationError("No se definio el mail en el contacto de la compania")
        #if denominacion:
        #    est.update( { 'denominacion': denominacion})
        return est
