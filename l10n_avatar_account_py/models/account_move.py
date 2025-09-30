# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

import logging
_logger = logging.getLogger(__name__)

import json

XMLGEN_MOVE_TYPES = {
    'entry': '0', 'out_invoice': '1', 'out_refund': '5', 
    'in_invoice': '4', 'in_refund': '0', 'out_receipt': '7', 'in_receipt': '0', 
}

DESC_TIDE_P = {
    '1': 'Factura', '2': 'Factura de exportación',
    '3': 'Factura de importación', '4': 'Autofactura',
    '5': 'Nota de crédito', '6': 'Nota de débito',
    '7': 'Nota de remisión', '8': 'Comprobante de retención',
}

DESC_TIDE_E = {
    '1': 'Factura electrónica', '2': 'Factura electrónica de exportación',
    '3': 'Factura electrónica de importación', '4': 'Autofactura electrónica',
    '5': 'Nota de crédito electrónica', '6': 'Nota de débito electrónica',
    '7': 'Nota de remisión electrónica', '8': 'Comprobante de retención electrónico',
}

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
    ], string="Condición de la operación", default='1')

    # Constancia de No Contribuyente
    l10n_avatar_py_taxpayer_number = fields.Char(
        string="Nº de Constancia", copy=False, store=True)
    l10n_avatar_py_taxpayer_control = fields.Char(
        string="Nº de Control", copy=False, store=True)
    l10n_avatar_py_taxpayer_startdate = fields.Date(
        string="Fecha de inicio de constancia", copy=False, store=True)
    l10n_avatar_py_taxpayer_enddate = fields.Date(
        string="Fecha fin de constancia", copy=False, store=True)

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


    # Confirmar
    l10n_avatar_py_date_post = fields.Datetime(string="Fecha de emisión", readonly=True, copy=False)

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
            if self.l10n_latam_document_type_id:
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
                x.journal_id.type == 'sale' or (
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

        return posted
        
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

    
    # JSON DE
    # B. Campos inherentes a la operación de Documentos Electrónicos (B001-B099)
    def _get_sifen_gOpeDE(self):
        gOpeDE = {}
        gOpeDE.update({ 'iTipEmi': int(self.l10n_avatar_py_itipemi) })
        field_info = self.fields_get(allfields=['l10n_avatar_py_itipemi'])['l10n_avatar_py_itipemi']
        selection_dict = dict(field_info['selection'])
        gOpeDE.update({ 'dDesTipEmi': selection_dict.get(self.l10n_avatar_py_itipemi) })
        if not self.l10n_avatar_py_dcodseg:
            raise ValidationError("No se generó el Código de seguridad (dCodSeg)")
        gOpeDE.update({ 'dCodSeg': self.l10n_avatar_py_dcodseg})
        if self.l10n_avatar_py_dinfoemi:
            gOpeDE.update({ 'dInfoEmi': self.l10n_avatar_py_dinfoemi})
        if self.l10n_avatar_py_dinfoemi:
            gOpeDE.update({ 'dInfoFisc': self.l10n_avatar_py_dinfofisc})
        return gOpeDE

    # C Campos de datos del Timbrado (C001-C099)
    def _get_sifen_gTimb(self, forReport=False):
        gTimb = {}
        if self.move_type == 'in_invoice':
            gTimb.update({ 'iTiDE': 1})
        elif self.move_type == 'out_invoice' and self.journal_id.l10n_avatar_py_poe_system in ('AFP','AFE'):
            gTimb.update({ 'iTiDE': 4})
        elif self.move_type == 'out_invoice':
            gTimb.update({ 'iTiDE': 1})
        elif self.move_type in ('in_refund','out_refund'):
            gTimb.update({ 'iTiDE': 5})
        dDesTiDE= DESC_TIDE_E[str(gTimb.get('iTiDE'))] if self.journal_id.l10n_avatar_py_poe_system in ('FAE','AFE') else DESC_TIDE_P[str(gTimb.get('iTiDE'))]
        gTimb.update({ 'dDesTiDE': dDesTiDE.upper() if forReport else dDesTiDE })
        dNumTim = self.l10n_avatar_py_authorization_code
        if dNumTim.split('-').__len__() == 2:
            gTimb.update({ 'dNumTim': dNumTim.split('-')[1]})
            gTimb.update({ 'dSerieNum': dNumTim.split('-')[0]})
        else:
            gTimb.update({ 'dNumTim': dNumTim})
        gTimb.update({ 'dEst': "%03d" % self.journal_id.l10n_avatar_py_branch})
        gTimb.update({ 'dPunExp': "%03d" % self.journal_id.l10n_avatar_py_dispatch_point})
        gTimb.update({ 'dNumDoc': "%07d" % self.sequence_number})
        gTimb.update({ 'dFeIniT': self.l10n_avatar_py_authorization_startdate})
        if self.journal_id.l10n_avatar_py_poe_system in ('FAP','AFP'):
            gTimb.update({ 'dFeFinT': self.l10n_avatar_py_authorization_enddate})
        return gTimb

    # D1 Campos inherentes a la operación comercial (D010-D099)
    def _get_sifen_gOpeCom(self):
        gOpeCom = {}
        if self._get_sifen_gTimb().get('') in (1,4):
            if not self.l10n_avatar_py_itiptra:
                raise ValidationError("No se determinó el Tipo de Transacción (iTipTra)")
            gOpeCom.update({ 'iTipTra': int(self.l10n_avatar_py_itiptra)})
        field_info = self.fields_get(allfields=['l10n_avatar_py_itiptra'])['l10n_avatar_py_itiptra']
        selection_dict = dict(field_info['selection'])
        gOpeCom.update({ 'dDesTipTra': selection_dict.get(self.l10n_avatar_py_itiptra)})
        gOpeCom.update({ 'iTImp': int(self.l10n_avatar_py_itimp)})
        field_info = self.fields_get(allfields=['l10n_avatar_py_itimp'])['l10n_avatar_py_itimp']
        selection_dict = dict(field_info['selection'])
        gOpeCom.update({ 'dDesTImp': selection_dict.get(self.l10n_avatar_py_itimp)})
        gOpeCom.update({ 'cMoneOpe': self.currency_id.name})
        gOpeCom.update({ 'dDesMoneOpe': self.currency_id.full_name})
        if self.currency_id.name != 'PYG':
            gOpeCom.update({ 'dCondTiCam': 1})
            gOpeCom.update({ 'dTiCam': round(1/self.invoice_currency_rate,2)})  
        if int(self.l10n_avatar_py_itiptra) == 9:
            gOpeCom.update({ 'iCondAnt': 1})
            gOpeCom.update({ 'dDesCondAnt': 'Anticipo Global'})
        return gOpeCom

    # D2 Campos que identifican al emisor del Documento Electrónico DE (D100-D129)
    def _get_sifen_gEmis(self):
        gEmis = {}
        Partner = self.company_id.partner_id
        Company = self.company_id
        gEmis.update({ 'dRucEmi': Partner.vat.split('-')[0]})
        gEmis.update({ 'dDVEmi': Partner.vat.split('-')[1]})
        gEmis.update({ 'iTipCont': Company.l10n_avatar_py_itipcont})
        gEmis.update({ 'cTipReg': Partner.l10n_avatar_py_taxpayer_type})
        if Company.l10n_avatar_py_is_edi_test and self.journal_id.l10n_avatar_py_poe_system in ('FAE','AFE'):
            gEmis.update({ 'dNomFanEmi': Partner.name })
            gEmis.update({ 'dNomEmi': 'DE generado en ambiente de prueba - sin valor comercial ni fiscal' })
        else:
            gEmis.update({ 'dNomEmi': Partner.name })
        gEmis.update({ 'dDirEmi': Partner.street })
        gEmis.update({ 'dNumCas': Partner.external_number or 0 })
        if Partner.street2:
            gEmis.update({ 'dCompDir1': Partner.street2 })
        gEmis.update({ 'cDepEmi': int(Partner.state_id.code) })
        gEmis.update({ 'dDesDepEmi': Partner.state_id.name })
        if Partner.municipality_id:
            gEmis.update({ 'cDisEmi': int(Partner.municipality_id.code) })
            gEmis.update({ 'dDesDisEmi': int(Partner.municipality_id.name) })
        gEmis.update({ 'cCiuEmi': int(Partner.city_id.code) })
        gEmis.update({ 'dDesCiuEmi': int(Partner.city_id.name) })
        gEmis.update( { "dTelEmi": Partner.phone or Partner.mobile})
        gEmis.update( { "dEmailE": Partner.email})
        return gEmis

    # D2.1 Campos que describen la actividad económica del emisor (D130-D139) -- Company
    def _get_sifen_gActEco( self):
        gActEco = []
        for rec in self.company_id.l10n_avatar_py_economic_activity_ids:
            actEco = {}
            actEco.update({ 'cActEco': rec.code})
            actEco.update({ 'dDesActEco': rec.name})
            gActEco.append(actEco)
        return gActEco

    # D2.2 Campos que identifican al responsable de la generación del DE (D140-D160) -- PENDIENTE

    # D3 Campos que identifican al receptor del Documento Electrónico DE (D200-D299)
    def _get_sifen_gDatRec(self):
        gDatRec = {}
        if self.journal_id.l10n_avatar_py_poe_system in ('AFP', 'AFE'):
            gDatRec = self._get_sifen_gDatRec_afa()
        else: 
            gDatRec = self._get_sifen_gDatRec_fa()
        return gDatRec

    def _get_sifen_gDatRec_fa(self):
        gDatRec = {}
        gDatRec.update(
            { 'iNatRec': 1 if self.partner_id.l10n_latam_identification_type_id.l10n_avatar_py_code == '99' else 2})
        if not self.l10n_avatar_py_itiope:
            raise ValidationError("Falta definir el Tipo de Operación (B2B/B2C/B2G/B2F)")
        gDatRec.update({ 'iTiOpe': int(self.l10n_avatar_py_itiope)})
        gDatRec.update({ 'cPaisRec': self.partner_id.country_id.alpha_code})
        gDatRec.update({ 'dDesPaisRe': self.partner_id.country_id.name})
        if self.partner_id.l10n_latam_identification_type_id.l10n_avatar_py_code == '99':
            gDatRec.update({ 'iTiContRec': 1 if not self.partner_id.is_company else 2})
            gDatRec.update({ 'dRucRec': self.partner_id.vat.split('-')[0]})
            gDatRec.update({ 'dDVRec': self.partner_id.vat.split('-')[1]})
        if self.partner_id.l10n_latam_identification_type_id.l10n_avatar_py_code != '99' and int(self.l10n_avatar_py_itiope) != 4:
            if not self.partner_id.l10n_latam_identification_type_id.l10n_avatar_py_code:
                raise ValidationError("Falta definir el tipo de identificación del contacto %s" % self.partner_id.name)
            gDatRec.update({ 'iTipIDRec': int(self.partner_id.l10n_latam_identification_type_id.l10n_avatar_py_code)})
            gDatRec.update({ 'dDTipIDRec': self.partner_id.l10n_latam_identification_type_id.name})
            if not self.partner_id.vat:
                raise ValidationError("Falta definir el número de identificación del contacto %s" % self.partner_id.name)
            gDatRec.update({ 'dNumIDRec': self.partner_id.vat})
        return gDatRec

    def _get_sifen_gDatRec_afa(self):
        gDatRec = {}
        if self.partner_id.l10n_latam_identification_type_id.l10n_avatar_py_code == '99':
            raise ValidationError("El contacto %s no puede ser contribuyente para una Autofactura" % self.partner_id.name)
        gDatRec.update({ 'iNatRec': 2})
        if self.l10n_avatar_py_itiope not in ('2','4'):
            raise ValidationError("Tipo de Operación inválida para una Autofactura (%s)" % self.l10n_avatar_py_itiope)
        gDatRec.update({ 'iTiOpe': int(self.l10n_avatar_py_itiope)})
        if not self.partner_id.country_id:
            raise ValidationError("No se declaró país para el contacto %s" % self.partner_id.country_id)
        gDatRec.update({ 'cPaisRec': self.partner_id.country_id.alpha_code})
        gDatRec.update({ 'dDesPaisRe': self.partner_id.country_id.name})
        if not self.partner_id.l10n_latam_identification_type_id:
            raise ValidationError("No se declaró el tipo de documento del contacto %s" % self.partner_id.name)
        gDatRec.update({ 'iTipIDRec': self.partner_id.l10n_latam_identification_type_id.l10n_avatar_py_code})
        field_info = self.partner_id.l10n_latam_identification_type_id.fields_get(allfields=['l10n_avatar_py_code'])['l10n_avatar_py_code']
        selection_dict = dict(field_info['selection'])
        gDatRec.update({ 'dDTipIDRec': selection_dict.get(self.partner_id.l10n_latam_identification_type_id.l10n_avatar_py_code)})
        if self.partner_id.l10n_latam_identification_type_id.l10n_avatar_py_code == '5':
            gDatRec.update({ 'dNumIDRec': '0'})
            gDatRec.update({ 'dNomRec': 'Sin Nombre'})
        else:
            if not self.partner_id.vat:
                raise ValidationError("No se declaró el número de documento del contacto %s" % self.partner_id.name)
            gDatRec.update({ 'dNumIDRec': self.partner_id.vat})
            gDatRec.update({ 'dNomRec': self.partner_id.name})
        return gDatRec

    # E7 Campos que describen la condición de la operación (E600-E699)
    def _get_sifen_gCamCond(self):
        gCamCond = {}
        if self.invoice_date_due and (self.invoice_date_due - (self.invoice_date or datetime.now())).days > 5:
            gCamCond.update({ 'iCondOpe': 2})
            gCamCond.update({ 'dDCondOpe': 'Crédito'})
            gCamCond.update({ 'gPagCred': self._get_sifen_gPagCred()})
        else:
            gCamCond.update({ 'iCondOpe': 1})
            gCamCond.update({ 'dDCondOpe': 'Contado'})
            gCamCond.update({ 'gPaConEIni': self._get_sifen_gPaConEIni()})
        return gCamCond

    # E7.1 Campos que describen la forma de pago de la operación al contado o del monto de la entrega inicial (E605-E619)
    def _get_sifen_gPaConEIni(self):
        gPaConEIni = {}
        gPaConEIni.update({ 'iTiPago': 1}) # Forzamos a pago efectivo
        gPaConEIni.update({ 'dDesTiPag': 'Efectivo'})
        gPaConEIni.update({ 'dMonTiPag': self.amount_total})
        gPaConEIni.update({ 'cMoneTiPag': self.currency_id.name})
        gPaConEIni.update({ 'dDMoneTiPag': self.currency_id.full_name})
        if self.currency_id.name != 'PYG':
            gPaConEIni.update({ 'dTiCamTiPag': round(1 / self.invoice_currency_rate, 2)})
        return gPaConEIni

    # E7.2 Campos que describen la operación a crédito (E640-E649)
    def _get_sifen_gPagCred(self):
        gPagCred = {}
        if self.invoice_payment_term_id:
            gPagCred.update({ 'iCondCred': 2}) #Cuotas
            gPagCred.update({ 'dDCondCred': 'Cuota'})
            gCuotas = self._get_sifen_gCuotas()
            gPagCred.update({ 'dCuotas': len(gCuotas)})
            gPagCred.update({ 'gCuotas': gCuotas})
        else: # Plazo
            gPagCred.update({ 'iCondCred': 1}) #Plazo
            gPagCred.update({ 'dDCondCred': 'Plazo'})
            gPagCred.update({ 'dPlazoCre': str(round((self.invoice_date_due - (self.invoice_date or datetime.now())).days,0)) + " días" })
        return gPagCred

    # E7.2.1 Campos que describen las cuotas (E650-E659)
    def _get_sifen_gCuotas(self):
        gCuotas = []
        sign = 1 if self.is_inbound(include_receipts=True) else -1
        invoice_payment_terms = self.invoice_payment_term_id._compute_terms(
                        date_ref=self.invoice_date or self.date or fields.Date.context_today(self),
                        currency=self.currency_id,
                        tax_amount_currency=self.amount_tax * sign,
                        tax_amount=self.amount_tax_signed,
                        untaxed_amount_currency=self.amount_untaxed * sign,
                        untaxed_amount=self.amount_untaxed_signed,
                        company=self.company_id,
                        cash_rounding=self.invoice_cash_rounding_id,
                        sign=sign
                    )
        for line in invoice_payment_terms['line_ids']:
            gCuota = {}
            gCuota.update({ 'cMoneCuo': self.currency_id.name})
            gCuota.update({ 'dDMoneCuo': self.currency_id.full_name})
            gCuota.update({ 'dMonCuota': line.get('foreign_amount')})
            gCuota.update({ 'dVencCuo': line.get('date').strftime("%Y-%m-%d")})
            gCuotas.append( gCuota)
        return gCuotas

    # H Campos que identifican al documento asociado (H001-H049)
    def _get_sifen_gCamDEAsoc(self):
        gCamDEAsoc = {}
        if self.move_type == 'out_refund' and self.reversed_entry_id.journal_id.l10n_avatar_py_poe_system == 'FAE':
            iTipDocAso = 1
            gCamDEAsoc.update({ 'iTipDocAso': iTipDocAso})
            gCamDEAsoc.update({ 'dDesTipDocAso': 'Electrónico'})
            gCamDEAsoc.update({ 'dCdCDERef': 'VALOR DEL CDC - PENDIENTE'})
        elif self.move_type == 'out_refund' and self.reversed_entry_id.journal_id.l10n_avatar_py_poe_system == 'FAP':
            iTipDocAso = 2
            gCamDEAsoc.update({ 'iTipDocAso': iTipDocAso})
            gCamDEAsoc.update({ 'dDesTipDocAso': 'Impreso'})
            gCamDEAsoc.update({ 'dNTimDI': self.reversed_entry_id.l10n_avatar_py_authorization_code})
            gCamDEAsoc.update({ 'dEstDocAso': ("%03d" % self.reversed_entry_id.journal_id.l10n_avatar_py_branch)})
            gCamDEAsoc.update({ 'dPExpDocAso': ("%03d" % self.reversed_entry_id.journal_id.l10n_avatar_py_dispatch_point)})
            gCamDEAsoc.update({ 'dNumDocAso': ("%07d" % self.reversed_entry_id.sequence_number)})
            gCamDEAsoc.update({ 'iTipoDocAso': 1 if self.reversed_entry_id.move_type == 'out_invoice' else 2})
            gCamDEAsoc.update({ 'dDTipoDocAso': 'Factura' if self.reversed_entry_id.move_type == 'out_invoice' else 'Nota de crédito'})
            gCamDEAsoc.update({ 'dFecEmiDI': self.reversed_entry_id.invoice_date.strftime("%Y-%m-%d")})
        elif self.move_type == 'in_invoice' and self.journal_id.l10n_avatar_py_poe_system in ('AFP','AFE'):
            iTipDocAso = 3
            gCamDEAsoc.update({ 'iTipDocAso': iTipDocAso})
            gCamDEAsoc.update({ 'dDesTipDocAso': 'Constancia Electrónica'})
        else:
            raise ValidationError("Tipo de documento asociado no contemplado")
        return gCamDEAsoc

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

    ############################################################


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
