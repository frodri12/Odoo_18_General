# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

import logging
_logger = logging.getLogger(__name__)

import json
from random import randint

XMLGEN_MOVE_TYPES = {
    'entry': '0', 'out_invoice': '1', 'out_refund': '5', 
    'in_invoice': '4', 'in_refund': '0', 'out_receipt': '7', 'in_receipt': '0', 
}

"""
DESC_TIDE_P = {
    '1': 'Factura', '2': 'Factura de exportación',
    '3': 'Factura de importación', '4': 'Autofactura',
    '5': 'Nota de crédito', '6': 'Nota de débito',
    '7': 'Nota de remisión', '8': 'Comprobante de retención',
}
"""

"""
DESC_TIDE_E = {
    '1': 'Factura electrónica', '2': 'Factura electrónica de exportación',
    '3': 'Factura electrónica de importación', '4': 'Autofactura electrónica',
    '5': 'Nota de crédito electrónica', '6': 'Nota de débito electrónica',
    '7': 'Nota de remisión electrónica', '8': 'Comprobante de retención electrónico',
}
"""

def date2time( date):
    time = datetime.now().strftime("%H%M%S")
    if date:
        return datetime.strptime(date.strftime("%Y%m%d") + time, "%Y%m%d%H%M%S")
    return date

class PyAccountMove(models.Model):

    _inherit = 'account.move'

    # Timbrado
    l10n_avatar_py_authorization_code = fields.Char(string="Timbrado")
    l10n_avatar_py_authorization_startdate = fields.Date(string="Fecha inicio de Timbrado")
    l10n_avatar_py_authorization_enddate = fields.Date(string="Fecha de fin de Timbrado")

    # Rate
    l10n_avatar_py_inverse_currency_rate = fields.Float(string='Inverse Currency Rate', readonly=True, store=True,
         compute="_compute_py_inverse_currency_rate", precompute=True, copy=False)

    # Retenciones
    l10n_avatar_py_withholding_ids = fields.One2many(
        'account.move.line', 'move_id', string='Withholdings',
        compute='_compute_l10n_avatar_py_withholding_ids',
        readonly=True
    )

    #
    l10n_avatar_py_itipemi = fields.Selection(
        [
            ('1','Normal'),('2','Contingencia')
        ], string="Tipo de emisión", default='1'
    )
    l10n_avatar_py_dcodseg = fields.Char(string="Código de seguridad", readonly=True)
    l10n_avatar_py_dinfoemi = fields.Text(string="Información de interés del emisor respecto al DE")
    l10n_avatar_py_dinfofisc = fields.Text(string="Información de interés del Fisco respecto al DE")
    l10n_avatar_py_itiptra = fields.Selection([
        ('1','Venta de mercadería'),('2','Prestación de servicios'),('3','Mixto (Venta de mercadería y servicios)'),
        ('4','Venta de activo fijo'),('5','Venta de divisas'),('6','Compra de divisas'),
        ('7','Promoción o entrega de muestras'),('8','Donación'),('9','Anticipo'),
        ('10','Compra de productos'),('11','Compra de servicios'),('12','Venta de crédito fiscal'),
        ('13','Muestras médicas (Art. 3 RG 24/2014)')
    ], string="Tipo de Transacción")
    l10n_avatar_py_itimp = fields.Selection([
        ('1','IVA'),('2','ISC'),('3','Ninguno'),('4','IVA - Renta'),
    ], string="Tipo de impuesto afectado", default="1")
    l10n_avatar_py_itiope = fields.Selection([
        ('1','B2B'),('2','B2C'),('3','B2G'),('4','B2G')
    ], string="Tipo de operación", compute='_compute_py_itiope')
    l10n_avatar_py_icondope = fields.Selection([
        ('1','Contado'), ('2','Crédito'),
    ], string="Condición de la operación", default="1")

    # Constancia de No Contribuyente
    l10n_avatar_py_taxpayer_number = fields.Char(
        string="Nº de Constancia", copy=False, store=True)
    l10n_avatar_py_taxpayer_control = fields.Char(
        string="Nº de Control", copy=False, store=True)
    l10n_avatar_py_taxpayer_startdate = fields.Date(
        string="Fecha de inicio de constancia", copy=False, store=True)
    l10n_avatar_py_taxpayer_enddate = fields.Date(
        string="Fecha fin de constancia", copy=False, store=True)

    # Confirmar
    l10n_avatar_py_date_post = fields.Datetime(string="Fecha de emisión", readonly=True, copy=False)

    # EDI
    l10n_avatar_py_edi_cdc = fields.Char(string="CDC", readonly=True)
    l10n_avatar_py_edi_state = fields.Selection([ 
        ('N', 'No aplica'), ('P', 'Pendiente de envio'),
        ('S', 'Enviado'), ('A', 'Aprobado'), ('O', 'Aprobado con observacion'),
        ('R', 'Rechazado'), ('E', 'Error')
        ], string="Estado del envio a la SET", readonly=True
    )
    l10n_avatar_py_edi_lote_ids = fields.One2many(
        'l10n_avatar_py_edi_lote', 'move_id', string="Numero de lote", copy=False
    )

    @api.onchange('partner_id')
    def _onchange_py_taxpayer(self):
        if not self.l10n_avatar_py_taxpayer_number:
            self.l10n_avatar_py_taxpayer_number = self.partner_id.l10n_avatar_py_taxpayer_number
        if not self.l10n_avatar_py_taxpayer_control:
            self.l10n_avatar_py_taxpayer_control = self.partner_id.l10n_avatar_py_taxpayer_control
        if not self.l10n_avatar_py_taxpayer_startdate:
            self.l10n_avatar_py_taxpayer_startdate = self.partner_id.l10n_avatar_py_taxpayer_startdate
        if not self.l10n_avatar_py_taxpayer_enddate:
            self.l10n_avatar_py_taxpayer_enddate = self.partner_id.l10n_avatar_py_taxpayer_enddate

    @api.depends('partner_id')
    def _compute_py_itiope(self):
        if not self.l10n_avatar_py_itiope:
            self.l10n_avatar_py_itiope = '1' if self.partner_id.is_company else '2'




    def _get_l10n_latam_documents_domain(self):
        self.ensure_one()
        domain = super()._get_l10n_latam_documents_domain()
        if self.journal_id.company_id.account_fiscal_country_id.code == "PY":
            domain = expression.AND([
                domain or [],
                self.journal_id._get_journal_codes_domain(),
            ])
        return domain

    def _is_manual_document_number(self):
        if self.country_code != 'PY':
            return super()._is_manual_document_number()

        if self.l10n_latam_use_documents and self.journal_id.type == 'purchase':
            if self.journal_id.l10n_avatar_py_poe_system in ['AFP', 'AFE']:
                return False
            else:
                return True
        
        return self.l10n_latam_use_documents and self.journal_id.type in ['purchase', 'sale'] and \
            not self.journal_id.l10n_avatar_py_poe_system

    def _get_starting_sequence(self):
        if self.journal_id.l10n_latam_use_documents and self.company_id.account_fiscal_country_id.code == "PY":
            if self.l10n_latam_document_type_id and self.journal_id.l10n_avatar_py_poe_system not in ('NTP'):
                return self._get_formatted_sequence()
        return super()._get_starting_sequence()

    def _get_formatted_sequence(self, number=0):
        return "%s %03d-%03d-%07d" % (self.l10n_latam_document_type_id.doc_code_prefix,
                                 self.journal_id.l10n_avatar_py_branch,
                                 self.journal_id.l10n_avatar_py_dispatch_point, number)

    def _get_last_sequence_domain(self, relaxed=False):
        where_string, param = super(PyAccountMove, self)._get_last_sequence_domain(relaxed)
        if self.company_id.account_fiscal_country_id.code == "PY" and self.l10n_latam_use_documents:
            where_string += " AND l10n_latam_document_type_id = %(l10n_latam_document_type_id)s"
            param['l10n_latam_document_type_id'] = self.l10n_latam_document_type_id.id or 0
        return where_string, param

    @api.onchange('l10n_latam_document_type_id', 'l10n_latam_document_number', 'partner_id')
    def _inverse_l10n_latam_document_number(self):
        super()._inverse_l10n_latam_document_number()

        to_review = self.filtered(lambda x: (
            x.l10n_latam_document_type_id
            and x.l10n_latam_document_number
            and (x.l10n_latam_manual_document_number or not x.highest_name)
            and x.l10n_latam_document_type_id.country_id.code == 'PY'
            and (
                ( x.journal_id.type == 'sale' and x.journal_id.l10n_avatar_py_poe_system not in ('NTP')) or (
                    x.journal_id.type == 'purchase'and x.journal_id.l10n_avatar_py_poe_system in ('AFP','AFE')
                )
            )
        ))
        for rec in to_review:
            number = str(rec.l10n_latam_document_type_id._format_document_number(rec.l10n_latam_document_number))
            current_est = int(number.split("-")[0])
            current_pos = int(number.split("-")[1])
            if current_pos != rec.journal_id.l10n_avatar_py_dispatch_point or current_est != self.journal_id.l10n_avatar_py_branch:
                invoices = self.search([('journal_id', '=', rec.journal_id.id), ('posted_before', '=', True)], limit=1)
                # If there is no posted before invoices the user can change the POS number (x.l10n_latam_document_number)
                if (not invoices):
                    rec.journal_id.l10n_avatar_py_branch = current_est
                    rec.journal_id.l10n_avatar_py_dispatch_point = current_pos
                    #rec.journal_id._onchange_set_short_name()
                # If not, avoid that the user change the POS number
                else:
                    raise UserError(_('The document number can not be changed for this journal, you can only modify'
                                      ' the POS number if there is not posted (or posted before) invoices'))

    # Validacion del IVA
    def _check_py_invoice_taxes( self):
        if self.move_type in ('in_invoice','in_refund','out_invoice','out_refund'):
            for line in self.mapped('invoice_line_ids').filtered(lambda x: x.display_type not in ('line_section', 'line_note')):
                vat_taxes = line.tax_ids.filtered(lambda x: x.tax_group_id.l10n_avatar_py_tax_type in ('0','5','10'))
                if len(vat_taxes) != 1:
                    raise UserError("Debería haber un solo impuesto del grupo IVA por línea")

    # Confirmar
    def _post(self, soft=True):
        py_invoices = self.filtered(lambda x: x.company_id.account_fiscal_country_id.code == "PY" and x.l10n_latam_use_documents)
        py_invoices._check_py_invoice_taxes()
        posted = super()._post(soft=soft)
        ## Logueo para ver que datos tenemos
        #_logger.error( "\n\n" + json.dumps(str(py_invoices.needed_terms), indent=2) + "\n\n")
        #_logger.error(py_invoices.needed_terms)

        #####_logger.error( "\n\n" + json.dumps(self._get_sifen_gCamCond(), indent=2) + "\n\n" )

        
        if not posted.l10n_avatar_py_date_post:
            if posted.invoice_date:
                posted.l10n_avatar_py_date_post = date2time( posted.invoice_date)
        if posted.journal_id.l10n_avatar_py_poe_system in ('FAP', 'AFP'):
            posted.l10n_avatar_py_edi_state = 'N'
        if posted.journal_id.l10n_avatar_py_poe_system in ('FAE', 'AFE'):
            posted.l10n_avatar_py_edi_state = 'P'
            posted._generate_dCodSeg()
            posted._compute_edi_lote()

        return posted
        
    def button_draft(self):
        super().button_draft()
        if self.l10n_avatar_py_edi_state  in ( 'S','A','O'):
            raise UserError("No se puede pasar a borrador un documento aprobado o en proceso de aprobacion")

    def button_cancel(self):
        super().button_cancel()
        if self.journal_id.l10n_avatar_py_poe_system in ('FAE', 'AFE'):
            if self.l10n_avatar_py_edi_state != 'E':
                raise UserError(_("Only draft journal entries can be cancelled."))
            # Falta enviar el evento de cancelacion

    # Retenciones
    @api.depends('line_ids')
    def _compute_l10n_avatar_py_withholding_ids(self):
        for move in self:
            move.l10n_avatar_py_withholding_ids = move.line_ids.filtered(lambda l: l.tax_line_id.l10n_avatar_py_withholding_payment_type)        

    def _onchange_py_authorization_code_from_company( self):
        self.l10n_avatar_py_authorization_code = self.company_id.partner_id.l10n_avatar_py_authorization_code
        self.l10n_avatar_py_authorization_startdate = self.company_id.partner_id.l10n_avatar_py_authorization_startdate
        self.l10n_avatar_py_authorization_enddate = self.company_id.partner_id.l10n_avatar_py_authorization_enddate

    def _onchange_py_authorization_code_from_partner( self):
        self.l10n_avatar_py_authorization_code = self.partner_id.l10n_avatar_py_authorization_code
        self.l10n_avatar_py_authorization_startdate = self.partner_id.l10n_avatar_py_authorization_startdate
        self.l10n_avatar_py_authorization_enddate = self.partner_id.l10n_avatar_py_authorization_enddate

    def _onchange_py_authorization_code_from_journal(self):
        self.l10n_avatar_py_authorization_code = self.journal_id.l10n_avatar_py_authorization_code
        self.l10n_avatar_py_authorization_startdate = self.journal_id.l10n_avatar_py_authorization_startdate
        self.l10n_avatar_py_authorization_enddate = self.journal_id.l10n_avatar_py_authorization_enddate

   # Timbrado
    @api.onchange('partner_id','journal_id','l10n_latam_document_type_id')
    def _onchange_py_authorization_code( self):

        journal_type = self.journal_id.type
        if not self.l10n_latam_use_documents:
            return
        elif journal_type not in ( 'sale', 'purchase'):
            return
        # Venta Electronico
        elif journal_type == 'sale' and self.journal_id.l10n_avatar_py_poe_system in ('FAE','REE', 'FEE', 'FIE', 'AFE'):
            if self.company_id.l10n_avatar_py_is_edi_test:
                return self._onchange_py_authorization_code_from_company()
            else:
                return self._onchange_py_authorization_code_from_journal()
        elif journal_type == 'sale':
            return self._onchange_py_authorization_code_from_journal()
        elif journal_type == 'purchase' and self.journal_id.l10n_avatar_py_poe_system == 'AFE':
            if self.company_id.l10n_avatar_py_is_edi_test:
                return self._onchange_py_authorization_code_from_company()
            else:
                return self._onchange_py_authorization_code_from_journal()
        elif journal_type == 'purchase' and self.journal_id.l10n_avatar_py_poe_system == 'AFP':
            return self._onchange_py_authorization_code_from_journal()
        elif journal_type == 'purchase':
            if self.partner_id.l10n_avatar_py_authorization_code:
                return self._onchange_py_authorization_code_from_partner()
  
    # Rate
    @api.depends('currency_id','company_currency_id','company_id','invoice_date')
    def _compute_py_inverse_currency_rate(self):
        """ Compute the inverse currency rate for the move """
        for move in self:
            if move.is_invoice( include_receipts=True):
                move.l10n_avatar_py_inverse_currency_rate = round(1 / self.env['res.currency']._get_conversion_rate(
                    from_currency=move.company_currency_id,
                    to_currency=move.currency_id,
                    company=move.company_id,
                    date=move._get_invoice_currency_rate_date(),
                ), 2)
            else:
                move.l10n_avatar_py_inverse_currency_rate = 1

    def _get_name_invoice_report(self):
        self.ensure_one()
        if self.l10n_latam_use_documents and self.company_id.account_fiscal_country_id.code == 'PY':
            return 'l10n_avatar_account_py.report_invoice_document'
        return super()._get_name_invoice_report()

    ## Reportes
    def _get_sifen_total(self):
        #
        dSubExe_F002 = 0.0
        dSub5_F004 = 0.0
        dSub10_F005 = 0.0
        for line in self.line_ids:
            if line.display_type != 'product':
                continue
            itemdata = line._get_sifen_data()
            # F002 = dSubExe = Subtotal de la operación exenta
            # Suma de todas las ocurrencias de EA008 (Valor total de la operación por ítem)
            # cuando la operación sea exenta (Si E731 = 3), más Todas las ocurrencias de
            # la Base Exenta (E737) cuando la operación sea Gravado Parcial (Si E731 = 4).
            dSubExe_F002 = dSubExe_F002 + ((itemdata.get('dTotOpeItem_EA008') or 0.0) if itemdata.get('iAfecIVA_E731') == 3 else 0.0)
            dSubExe_F002 = dSubExe_F002 + ((itemdata.get('dBasExe_E737') or 0.0) if itemdata.get('iAfecIVA_E731') == 4 else 0.0)
            # F004 = dSub5 = Subtotal de la operación con IVA incluido a la tasa 5%
            # Suma de todas las ocurrencias de EA008 (Valor total de la operación por ítem) cuando la operación sea a
            # la tasa del 5% (E734=5) y (Si E731 = 1), más todas las ocurrencias de (E735 + E736) cuando la
            # operación sea a la tasa del 5% (E734=5) y (Si E731 = 4).
            if itemdata.get('dTasaIVA_E734') == 5:
                dSub5_F004 = dSub5_F004 + ((itemdata.get('dTotOpeItem_EA008') or 0.0) if itemdata.get('iAfecIVA_E731') == 1 else 0.0)
                dSub5_F004 = dSub5_F004 + ((itemdata.get('dBasGravIVA_E735') or 0.0) + (itemdata.get('dLiqIVAItem_E736') or 0.0) if itemdata.get('iAfecIVA_E731') == 4 else 0.0)
            # F005 = dSub10 = Subtotal de la operación con IVA incluido a la tasa 10%
            # Suma de todas las ocurrencias de EA008 (Valor total de la operación por ítem) cuando la operación sea a
            # la tasa del 10% (E734=10) y (Si E731 = 1), más todas las ocurrencias de (E735 + E736) cuando la
            # operación sea a la tasa del 10% (E734=10) y (Si E731 = 4).
            # No debe existir el campo si D013 ≠ 1 o D013 ≠ 5
            if itemdata.get('dTasaIVA_E734') == 10:
                dSub10_F005 = dSub10_F005 + ((itemdata.get('dTotOpeItem_EA008') or 0.0) if itemdata.get('iAfecIVA_E731') == 1 else 0.0)
                dSub10_F005 = dSub10_F005 + ((itemdata.get('dBasGravIVA_E735') or 0.0) + (itemdata.get('dLiqIVAItem_E736') or 0.0) if itemdata.get('iAfecIVA_E731') == 4 else 0.0)
        #
        return {
            'dSubExe_F002': dSubExe_F002,
            'dSub5_F004': dSub5_F004,
            'dSub10_F005': dSub10_F005,
        }


    ### EDI
    def _generate_dCodSeg(self):
        pin_length = 9
        number_max = (10**pin_length) - 1
        number = randint( 0, number_max)
        delta = (pin_length - len(str(number))) * '0'
        random_code = '%s%s' % (delta,number)
        condition = self._validate_dCodSeg( random_code)
        if condition:
            self._generate_dCodSeg()
        self.l10n_avatar_py_dcodseg = random_code
        return random_code
    
    def _validate_dCodSeg( self, code):
        acc = self.env['account.move'].search([('l10n_avatar_py_dcodseg', '=', code)])
        if len(acc) > 0:
            return True
        else:
            return False

    def _get_account_edi(self):
        return self.env['l10n_avatar_py_account_edi']

    """
    ###############
    def _get_xmlgen_ActividadesEconomicas(self):
        act = []
        for rec in self.company_id.l10n_avatar_py_economic_activity_ids:
            v = {}
            v.update( { 'codigo': rec.code}) #D131
            v.update( { 'descripcion': rec.name}) #D132
            act.append( v)
        if len(act) == 0:
            raise ValidationError("No se definieron las actividades económicas")
        return act
    """

    """
    ###########################################
    def _get_xmlgen_json(self):
        params = { }
        params.update( { "version": 150 })
        params.update( { "ruc": self.company_id.partner_id.vat }) #D101
        if self.company_id.l10n_avatar_py_is_edi_test:
            params.update( { "nombreFantasia": self.company_id.partner_id.name }) #D106
            params.update( { "razonSocial": "DE generado en ambiente de prueba - sin valor comercial ni fiscal" })
        else:
            params.update( { "razonSocial": self.company_id.partner_id.name }) #D105
        params.update( { "actividadesEconomicas": self._get_xmlgen_ActividadesEconomicas() })
        if not self.l10n_avatar_py_authorization_code or not self.l10n_avatar_py_authorization_startdate:
            raise ValidationError("No se especificaron los valores del Timbrado")
        params.update( { "timbradoNumero": self.l10n_avatar_py_authorization_code })
        params.update( { "timbradoFecha": self.l10n_avatar_py_authorization_startdate }) #D103
        params.update( { "tipoContribuyente": 2 if self.company_id.partner_id.is_company else 1 })
        tipoRegimen = self.company_id.partner_id.l10n_avatar_py_taxpayer_type
        if tipoRegimen and int(tipoRegimen) > 0:
            params.update( { "tipoRegimen": int(tipoRegimen) }) #D104
        establecimientos = []
        establecimientos.append( self.journal_id._get_xmlgen_Establecimiento())
        params.update( { "establecimientos": establecimientos})
        data = {}
        tipoDocumento = int(XMLGEN_MOVE_TYPES[self.move_type])
        data.update( { 'tipoDocumento': tipoDocumento}) #C002
        options = {}
        all_json = {}
        return all_json

    """
    ############################################################

    """

    # E4 Campos que componen la Autofactura Electrónica AFE (E300-E399)
    def _get_sifen_gCamAE(self):
        gCamAE = {}
        if self.partner_id.country_id.code == 'PY':
            gCamAE.update({ 'iNatVen': 1})
            gCamAE.update({ 'dDesNatVen': 'No contribuyente'})
        else:
            gCamAE.update({ 'iNatVen': 2})
            gCamAE.update({ 'dDesNatVen': 'Extranjero'})
        gCamAE.update({ 'iTipIDVen': self.partner_id.l10n_latam_identification_type_id.l10n_avatar_py_code})
        gCamAE.update({ 'dDTipIDVen': self.partner_id.l10n_latam_identification_type_id.name})
        gCamAE.update({ 'dNumIDVen': self.partner_id.vat})
        gCamAE.update({ 'dNomVen': self.partner_id.name})
        partner = self.partner_id
        if self.partner_id.country_id.code != 'PY':
            partner = self.journal_id.l10n_avatar_py_address_id
        gCamAE.update({ 'dDirVen': partner.street})
        gCamAE.update({ 'dNumCasVen': partner.external_number if partner.external_number else 0})
        gCamAE.update({ 'cDepVen': partner.state_id.code})
        gCamAE.update({ 'dDesDepVen': partner.state_id.name})
        gCamAE.update({ 'cDisVen': partner.municipality_id.code})
        gCamAE.update({ 'dDesDisVen': partner.municipality_id.name})
        gCamAE.update({ 'cCiuVen': partner.city_id.code})
        gCamAE.update({ 'dDesCiuVen': partner.city_id.name})
        #
        gCamAE.update({ 'dDirProv': self.journal_id.l10n_avatar_py_address_id.street})
        gCamAE.update({ 'cDepProv': self.journal_id.l10n_avatar_py_address_id.state_id.code})
        gCamAE.update({ 'dDesDepProv': self.journal_id.l10n_avatar_py_address_id.state_id.name})
        gCamAE.update({ 'cDisProv': self.journal_id.l10n_avatar_py_address_id.municipality_id.code})
        gCamAE.update({ 'dDesDisProv': self.journal_id.l10n_avatar_py_address_id.municipality_id.name})
        gCamAE.update({ 'cCiuProv': self.journal_id.l10n_avatar_py_address_id.city_id.code})
        gCamAE.update({ 'dDesCiuProv': self.journal_id.l10n_avatar_py_address_id.city_id.name})
        return gCamAE
    """

    def _compute_edi_lote(self):
        if not self.l10n_avatar_py_edi_lote_ids:
            self.env['l10n_avatar_py_edi_lote'].create({
                'move_id': self.id,
            })
        self.l10n_avatar_py_edi_lote_ids = self.env['l10n_avatar_py_edi_lote'].search([('move_id', '=',self.id)])

    def action_py_edi_timbrado(self):
        edi = self._get_account_edi()
        # Generar el json
        all_json = edi._get_sifen_xmlgen( move=self)
        self.l10n_avatar_py_edi_lote_ids.request_json = all_json
        # Enviar el lote
        edi._process_sifen_ResEnviLoteDe(move=self, data=all_json)
        if self.l10n_avatar_py_edi_lote_ids.resenvilotede_dcodres == '0300':
            # Lote generado con exito
            self.message_post(body="Lote %s generado con exito" % self.l10n_avatar_py_edi_lote_ids.resenvilotede_dprotconslote)
            self.l10n_avatar_py_edi_state = 'S'
        else:
            # Error en la generacion del lote
            self.message_post(body="Error en la generacion del lote [%s]" % self.l10n_avatar_py_edi_lote_ids.resenvilotede_dcodres + ' - ' + self.l10n_avatar_py_edi_lote_ids.resenvilotede_dmsgres)
        return

    def action_py_edi_read_lote(self):
        edi = self._get_account_edi()
        all_json = {}
        all_json.update({ 'empresa': self.company_id.partner_id.vat.split('-')[0]})
        all_json.update({ 'servicio': 'lote'})
        all_json.update({ 'lote': self.l10n_avatar_py_edi_lote_ids.lote_number})
        edi._get_sifen_ResEnviConsLoteDe( all_json, self.l10n_avatar_py_edi_lote_ids, self.company_id.l10n_avatar_py_is_edi_test)
        if self.l10n_avatar_py_edi_lote_ids.resenviconslotede_dcodreslot == '0362':
            # Lote procesado
            resenviconslotede_destrec = self.l10n_avatar_py_edi_lote_ids.resenviconslotede_destrec
            if resenviconslotede_destrec != None and 'bserv' in resenviconslotede_destrec:
                self.l10n_avatar_py_edi_state = 'O'
            elif resenviconslotede_destrec != None and resenviconslotede_destrec[:1] == 'R':
                self.l10n_avatar_py_edi_state = 'R'
            elif resenviconslotede_destrec != None and resenviconslotede_destrec[:1] == 'A':
                self.l10n_avatar_py_edi_state = 'A'
        elif self.l10n_avatar_py_edi_lote_ids.resenviconslotede_dcodreslot == '0361':
            # Todavia no termino.  No hacer nada
            a = 1
        else:
            # Algo parece que salio mal. Rechazar
            self.l10n_avatar_py_edi_state = 'R'
        return
