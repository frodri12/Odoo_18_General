# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.addons.account.models.account_move import AccountMove
from odoo.addons.account.models.account_move_line import AccountMoveLine
from odoo.addons.account.models.account_journal import AccountJournal
from odoo.addons.base.models.res_partner import Partner
from odoo.addons.base.models.res_company import Company
from odoo.addons.l10n_avatar_account_py.models.l10n_avatar_py_edi_lote import PyEdiLote
from datetime import datetime
import datetime as dt

import logging
_logger = logging.getLogger(__name__)

from os import path
import json

import requests

DESC_TIDE_E = {
    '1': 'Factura electrónica', '2': 'Factura electrónica de exportación',
    '3': 'Factura electrónica de importación', '4': 'Autofactura electrónica',
    '5': 'Nota de crédito electrónica', '6': 'Nota de débito electrónica',
    '7': 'Nota de remisión electrónica', '8': 'Comprobante de retención electrónico',
}

DESC_TIDE_P = {
    '1': 'Factura', '2': 'Factura de exportación',
    '3': 'Factura de importación', '4': 'Autofactura',
    '5': 'Nota de crédito', '6': 'Nota de débito',
    '7': 'Nota de remisión', '8': 'Comprobante de retención',
}

class PyAccountEdi(models.AbstractModel):

    _name = 'l10n_avatar_py_account_edi'
    _description = 'l10n_avatar_py_account_edi'

    # B. Campos inherentes a la operación de Documentos Electrónicos (B001-B099)
    def _get_sifen_gOpeDE(self, move:AccountMove, xmlgen=False):
        """
			'gOpeDE': {             // B001    {
			    'iTipEmi': 'N',     // B002        "tipoEmision" : 1,
				'dDesTipEmi': 'N',  // B003
				'dCodSeg': 'N',     // B004        "codigoSeguridadAleatorio" : "298398",
				'dInfoEmi': 'A',    // B005
				'dInfoFisc': 'A',   // B006
			},                                 },
        """
        gOpeDE = {}
        gOpeDE.update({ 'iTipEmi': int(move.l10n_avatar_py_itipemi) })
        field_info = move.fields_get(allfields=['l10n_avatar_py_itipemi'])['l10n_avatar_py_itipemi']
        selection_dict = dict(field_info['selection'])
        gOpeDE.update({ 'dDesTipEmi': selection_dict.get(move.l10n_avatar_py_itipemi) })
        if not move.l10n_avatar_py_dcodseg:
            raise ValidationError("No se generó el Código de seguridad (dCodSeg)")
        gOpeDE.update({ 'dCodSeg': move.l10n_avatar_py_dcodseg})
        if move.l10n_avatar_py_dinfoemi:
            gOpeDE.update({ 'dInfoEmi': move.l10n_avatar_py_dinfoemi})
        if move.l10n_avatar_py_dinfoemi:
            gOpeDE.update({ 'dInfoFisc': move.l10n_avatar_py_dinfofisc})
        if xmlgen:
            rec_xmlgen = {}
            rec_xmlgen.update({ 'tipoEmision': gOpeDE.get('iTipEmi')})
            rec_xmlgen.update({ 'codigoSeguridadAleatorio': gOpeDE.get('dCodSeg')})
            return rec_xmlgen
        return gOpeDE

    # C Campos de datos del Timbrado (C001-C099)
    def _get_sifen_gTimb(self, move:AccountMove, xmlgen=False):
        """
			'gTimb': {            // C001    {
			    'iTiDE': 'N',     // C002        "tipoDocumento" : 1,
				'dDesTiDE': 'A',  // C003
				'dNumTim': 'N',   // C004        "timbradoNumero" : "12558946",
				'dEst': 'A',      // C005        "establecimiento" : "001",
				'dPunExp': 'A',   // C006        "punto" : "001",
				'dNumDoc': 'A',   // C007        "numero" : "0000001",
				'dSerieNum': 'A', // C010        "serie": 'AA',
				'dFeIniT': 'F',   // C008        "timbradoFecha" : "2022-08-25",
			},                               },
        """
        gTimb = {}
        is_afa = True if move.journal_id.l10n_avatar_py_poe_system in ('AFP','AFE') else False
        is_edi = True if move.journal_id.l10n_avatar_py_poe_system in ('FAE','AFE') else False
        if move.move_type == 'in_invoice':
            gTimb.update({ 'iTiDE': 1})
        elif move.move_type == 'out_invoice' and is_afa:
            gTimb.update({ 'iTiDE': 4})
        elif move.move_type == 'out_invoice':
            gTimb.update({ 'iTiDE': 1})
        elif move.move_type in ('in_refund','out_refund'):
            gTimb.update({ 'iTiDE': 5})
        dDesTiDE= DESC_TIDE_E[str(gTimb.get('iTiDE'))] if is_edi else DESC_TIDE_P[str(gTimb.get('iTiDE'))]
        gTimb.update({ 'dDesTiDE': dDesTiDE.upper() if xmlgen else dDesTiDE })
        dNumTim = move.l10n_avatar_py_authorization_code
        if dNumTim.split('-').__len__() == 2:
            gTimb.update({ 'dNumTim': dNumTim.split('-')[1]})
            gTimb.update({ 'dSerieNum': dNumTim.split('-')[0]})
        else:
            gTimb.update({ 'dNumTim': dNumTim})
        gTimb.update({ 'dEst': "%03d" % move.journal_id.l10n_avatar_py_branch})
        gTimb.update({ 'dPunExp': "%03d" % move.journal_id.l10n_avatar_py_dispatch_point})
        gTimb.update({ 'dNumDoc': "%07d" % move.sequence_number})
        gTimb.update({ 'dFeIniT': move.l10n_avatar_py_authorization_startdate.strftime("%Y-%m-%d")})
        if move.journal_id.l10n_avatar_py_poe_system in ('FAP','AFP'):
            gTimb.update({ 'dFeFinT': move.l10n_avatar_py_authorization_enddate})
        if xmlgen:
            rec_xmlgen  = {}
            if gTimb.get('iTiDE') != None:
                rec_xmlgen.update({ 'tipoDocumento': gTimb.get('iTiDE')})
            if gTimb.get('dNumTim') != None:
                rec_xmlgen.update({ 'timbradoNumero': gTimb.get('dNumTim')})
            if gTimb.get('dEst') != None:
                rec_xmlgen.update({ 'establecimiento': gTimb.get('dEst')})
            if gTimb.get('dPunExp') != None:
                rec_xmlgen.update({ 'punto': gTimb.get('dPunExp')})
            if gTimb.get('dNumDoc') != None:
                rec_xmlgen.update({ 'numero': gTimb.get('dNumDoc')})
            if gTimb.get('dSerieNum') != None:
                rec_xmlgen.update({ 'serie': gTimb.get('dSerieNum')})
            if gTimb.get('dFeIniT') != None:
                rec_xmlgen.update({ 'timbradoFecha': gTimb.get('dFeIniT')})
            return rec_xmlgen
        return gTimb

    # D Campos Generales del Documento Electrónico DE (D001-D299)
    def _get_sifen_dFeEmiDE( self, move:AccountMove, xmlgen=False):
        """
			'gDatGralOpe': {       // D001
			    'dFeEmiDE': 'F',   // D002
				'gOpeCom': {},     // D010
				'gEmis': {},       // D100
				'gDatRec': {},     // D200
			},
        """
        dFeEmiDE = {}
        return dFeEmiDE

    # D1 Campos inherentes a la operación comercial (D010-D099)
    def _get_sifen_gOpeCom(self, move:AccountMove, xmlgen=False):
        """
				'gOpeCom': {            // D010    {
				    'iTipTra': 'N',     // D011        "tipoTransaccion" : 1,
					'dDesTipTra': 'A',  // D012
					'iTImp': 'N',       // D013        "tipoImpuesto" : 1,
					'dDesTImp': 'A',    // D014
					'cMoneOpe': 'A',    // D015        "moneda" : "PYG",
					'dDesMoneOpe': 'A', // D016
					'dCondTiCam': 'N',  // D017        "condicionTipoCambio": 1,
					'dTiCam': 'N',      // D018        "cambio": 6700,
					'iCondAnt': 'N',    // D019        "condicionAnticipo" : 1,
					'dDesCondAnt': 'A', // D020
				},                                 },
        """
        gOpeCom = {}
        if move.move_type in ('in_invoice','out_invoice'):
            if not move.l10n_avatar_py_itiptra:
                raise ValidationError("No se determinó el Tipo de Transacción (iTipTra)")
            gOpeCom.update({ 'iTipTra': int(move.l10n_avatar_py_itiptra)})
        field_info = move.fields_get(allfields=['l10n_avatar_py_itiptra'])['l10n_avatar_py_itiptra']
        selection_dict = dict(field_info['selection'])
        gOpeCom.update({ 'dDesTipTra': selection_dict.get(move.l10n_avatar_py_itiptra)})
        gOpeCom.update({ 'iTImp': int(move.l10n_avatar_py_itimp)})
        field_info = move.fields_get(allfields=['l10n_avatar_py_itimp'])['l10n_avatar_py_itimp']
        selection_dict = dict(field_info['selection'])
        gOpeCom.update({ 'dDesTImp': selection_dict.get(move.l10n_avatar_py_itimp)})
        gOpeCom.update({ 'cMoneOpe': move.currency_id.name})
        gOpeCom.update({ 'dDesMoneOpe': move.currency_id.full_name})
        if move.currency_id.name != 'PYG':
            gOpeCom.update({ 'dCondTiCam': 1})
            gOpeCom.update({ 'dTiCam': round(1/move.invoice_currency_rate,2)})  
        if int(move.l10n_avatar_py_itiptra) == 9:
            gOpeCom.update({ 'iCondAnt': 1})
            gOpeCom.update({ 'dDesCondAnt': 'Anticipo Global'})
        if xmlgen:
            rec_xmlgen = {}
            if gOpeCom.get('iTipTra') != None:
                rec_xmlgen.update({ 'tipoTransaccion':gOpeCom['iTipTra'] })
            if gOpeCom.get('iTImp') != None:
                rec_xmlgen.update({ 'tipoImpuesto':gOpeCom['iTImp'] })
            if gOpeCom.get('cMoneOpe') != None:
                rec_xmlgen.update({ 'moneda':gOpeCom['cMoneOpe'] })
            if gOpeCom.get('dCondTiCam') != None:
                rec_xmlgen.update({ 'condicionTipoCambio':gOpeCom['dCondTiCam'] })
            if gOpeCom.get('dTiCam') != None:
                rec_xmlgen.update({ 'cambio':gOpeCom['dTiCam'] })
            if gOpeCom.get('iCondAnt') != None:
                rec_xmlgen.update({ 'condicionAnticipo':gOpeCom['iCondAnt'] })
            return rec_xmlgen
        return gOpeCom

    # D2 Campos que identifican al emisor del Documento Electrónico DE (D100-D129)
    def _get_sifen_gEmis(self, company:Company, xmlgen=False, is_edi=True, establecimiento=1):
        """
				'gEmis': {              // D100    {
				    'dRucEm': 'A',      // D101        "ruc" : "80069563-1",
					'dDVEmi': 'N',      // D102
					'iTipCont': 'N',    // D103        "tipoContribuyente" : 2,
					'cTipReg': 'N',     // D104        "tipoRegimen" : 8,
					'dNomEmi': 'A',     // D105        "razonSocial" : "DE generado en ambiente de prueba - sin valor comercial ni fiscal",
					'dNomFanEmi': 'A',  // D106        "nombreFantasia" : "TIPS S.A. TECNOLOGIA Y SERVICIOS",
                                                       "establecimientos" : [{
                                                           "codigo" : "001",
					'dDirEmi': 'A',     // D107            "direccion" : "Barrio Carolina",
					'dNumCas': 'N',     // D108            "numeroCasa" : "0",
					'dCompDir1': 'A',   // D109            "complementoDireccion1" : "Entre calle 2",
					'dCompDir2': 'A',   // D110            "complementoDireccion2" : "y Calle 7",
					'cDepEmi': 'N',     // D111            "departamento" : 11,
					'dDesDepEmi': 'A',  // D112
					'cDisEmi': 'N',     // D113            "distrito" : 145,
					'dDesDisEmi': 'A',  // D114
					'cCiuEmi': 'N',     // D115            "ciudad" : 3432,
					'dDesCiuEmi': 'A',  // D116
					'dTelEmi': 'A',     // D117            "telefono" : "0973-527155",
					'dEmailE': 'A',     // D118            "email" : "tips@tips.com.py, tips@gmail.com",
					'dDenSuc': 'A',     // D119            "denominacion" : "Sucursal 1",
                                                       }],
					'gActEco': [],      // D130
					'gRespDE': {},      // D140
				},                                 },
        """
        gEmis = {}
        rec_xmlgen = {}
        partnerId = company.partner_id
        #Company = move.company_id
        gEmis.update({ 'dRucEmi': partnerId.vat.split('-')[0]})
        gEmis.update({ 'dDVEmi': partnerId.vat.split('-')[1]})
        gEmis.update({ 'iTipCont': company.l10n_avatar_py_itipcont})
        rec_xmlgen.update({ 'ruc': partnerId.vat})
        rec_xmlgen.update({ 'tipoContribuyente': company.l10n_avatar_py_itipcont})
        if partnerId.l10n_avatar_py_taxpayer_type and partnerId.l10n_avatar_py_taxpayer_type > '0':
            gEmis.update({ 'cTipReg': partnerId.l10n_avatar_py_taxpayer_type})
            rec_xmlgen.update({ 'tipoRegimen': partnerId.l10n_avatar_py_taxpayer_type})
        
        if company.l10n_avatar_py_is_edi_test and is_edi:
            gEmis.update({ 'dNomFanEmi': partnerId.name })
            gEmis.update({ 'dNomEmi': 'DE generado en ambiente de prueba - sin valor comercial ni fiscal' })
            rec_xmlgen.update({ 'nombreFantasia': gEmis['dNomFanEmi']})
        else:
            gEmis.update({ 'dNomEmi': partnerId.name })
        rec_xmlgen.update({ 'razonSocial': gEmis['dNomEmi']})
        gEmis.update({ 'dDirEmi': partnerId.street })
        gEmis.update({ 'dNumCas': partnerId.external_number or 0 })
        rec_est = {}
        rec_est.update({ 'direccion': gEmis['dDirEmi']})
        rec_est.update({ 'numeroCasa': gEmis['dNumCas']})
        if Partner.street2:
            gEmis.update({ 'dCompDir1': partnerId.street2 })
            rec_est.update({ 'complementoDireccion1': gEmis['dCompDir1']})
        gEmis.update({ 'cDepEmi': int(partnerId.state_id.code) })
        gEmis.update({ 'dDesDepEmi': partnerId.state_id.name })
        rec_est.update({ 'departamento': gEmis['cDepEmi']})
        if partnerId.municipality_id:
            gEmis.update({ 'cDisEmi': int(partnerId.municipality_id.code) })
            gEmis.update({ 'dDesDisEmi': partnerId.municipality_id.name })
            rec_est.update({ 'distrito': gEmis['cDisEmi']})
        gEmis.update({ 'cCiuEmi': int(partnerId.city_id.code) })
        gEmis.update({ 'dDesCiuEmi': partnerId.city_id.name })
        rec_est.update({ 'ciudad': gEmis['cCiuEmi']})
        gEmis.update( { "dTelEmi": partnerId.phone or partnerId.mobile})
        gEmis.update( { "dEmailE": partnerId.email})
        rec_est.update({ 'telefono': gEmis['dTelEmi']})
        rec_est.update({ 'email': gEmis['dEmailE']})
        if xmlgen:
            rec_est.update({ 'codigo': "%03d" % establecimiento})
            est = []
            est.append(rec_est)
            rec_xmlgen.update({ 'establecimientos': est})
            return rec_xmlgen
        return gEmis

    # D2.1 Campos que describen la actividad económica del emisor (D130-D139) -- Company
    def _get_sifen_gActEco( self, company:Company, xmlgen=False):
        """
					'gActEco': [                // D130    "actividadesEconomicas" : [
					    {                                      {
						    'cActEco': 'A',     // D131            "codigo": "1254",
							'dDesActEco': 'A',  // D132            "descripcion": "Desarrollo de Software",
						},                                     },
					],                                     ],
        """
        gActEco = []
        for rec in company.l10n_avatar_py_economic_activity_ids:
            actEco = {}
            actEco.update({ 'cActEco': rec.code})
            actEco.update({ 'dDesActEco': rec.name})
            if xmlgen:
                rec_xmlgen= {}
                rec_xmlgen.update({ 'codigo': rec.code})
                rec_xmlgen.update({ 'descripcion': rec.name})
                gActEco.append(rec_xmlgen)
            else:
                gActEco.append(actEco)
        return gActEco

    # D2.2 Campos que identifican al responsable de la generación del DE (D140-D160) -- PENDIENTE
    def _get_sifen_gRespDE( self, xmlgen=False):
        """
					'gRespDE': {              // D140    "usuario" : {
					    'iTipIDRespDE': 'N',  // D141        "documentoTipo" : 1,
						'dDTipIDRespDE': 'A', // D142
						'dNumIDRespDE': 'A',  // D143        "documentoNumero" : "157264",
						'dNomRespDE': 'A',    // D144        "nombre" : "Marcos Jara",
						'dCarRespDE': 'A',    // D145        "cargo" : "Vendedor",
					},                                   },
        """
        gRespDE = {}
        return gRespDE

    # D3 Campos que identifican al receptor del Documento Electrónico DE (D200-D299)
    def _get_sifen_gDatRec(self, move:AccountMove, xmlgen=False):
        """
				'gDatRec': {            // D200    "cliente" : {
				    'iNatRec': 'N',     // D201        "contribuyente" : true,
					'iTiOpe': 'N',      // D202        "tipoOperacion" : 1,
					'cPaisRec': 'A',    // D203        "pais" : "PRY",
					'dDesPaisRe': 'A',  // D204
					'iTiContRec': 'N',  // D205        "tipoContribuyente" : 1,
					'dRucRec': 'A',     // D206        "ruc" : "2005001-1",
					'dDVRec': 'N',      // D207
					'iTipIDRec': 'N',   // D208        "documentoTipo" : 1,
					'dDTipIDRec': 'A',  // D209        
					'dNumIDRec': 'A',   // D210        "documentoNumero" : "2324234",
					'dNomRec': 'A',     // D211        "razonSocial" : "Marcos Adrian Jara Rodriguez",
					'dNomFanRec': 'A',  // D212        "nombreFantasia" : "Marcos Adrian Jara Rodriguez",
					'dDirRec': 'A',     // D213        "direccion" : "Avda Calle Segunda y Proyectada",
					'dNumCasRec': 'N',  // D218        "numeroCasa" : "1515",
					'cDepRec': 'N',     // D219        "departamento" : 11,
					'dDesDepRec': 'A',  // D220
					'cDisRec': 'N',     // D221        "distrito" : 143,
					'dDesDisRec': 'A',  // D222
					'cCiuRec': 'N',     // D223        "ciudad" : 3344,
					'dDesCiuRec': 'A',  // D224
					'dTelRec': 'A',     // D214        "telefono" : "061-575903",
					'dCelRec': 'A',     // D215        "celular" : "0973-809103",
					'dEmailRec': 'A',   // D216        "email" : "cliente@empresa.com, cliente@personal.com",
					'dCodCliente': 'A', // D217        "codigo" : "1548"
				},                                 },
        """
        gDatRec = {}
        partnerId = move.partner_id
        journalId = move.journal_id
        is_afa = True if journalId.l10n_avatar_py_poe_system in ('AFP', 'AFE') else False
        if not partnerId.l10n_latam_identification_type_id.l10n_avatar_py_code:
            raise ValidationError("Falta definir el tipo de identificación del contacto %s" % move.partner_id.name)
        if partnerId.l10n_latam_identification_type_id.l10n_avatar_py_code == 99:
            if is_afa:
                raise ValidationError("El contacto %s no puede ser contribuyente para una Autofactura" % partnerId.name)
            gDatRec.update({ 'iNatRec': 1})
        else:
            gDatRec.update({ 'iNatRec': 2})
        if not move.l10n_avatar_py_itiope:
            raise ValidationError("Falta definir el Tipo de Operación (B2B/B2C/B2G/B2F)")
        if move.l10n_avatar_py_itiope not in ('2','4') and is_afa:
            raise ValidationError("Tipo de Operación inválida para una Autofactura (%s)" % move.l10n_avatar_py_itiope)
        gDatRec.update({ 'iTiOpe': int(move.l10n_avatar_py_itiope)})
        if not partnerId.country_id:
            raise ValidationError("No se declaró país para el contacto %s" % partnerId.name)
        gDatRec.update({ 'cPaisRec': partnerId.country_id.alpha_code})
        gDatRec.update({ 'dDesPaisRe': partnerId.country_id.name})
        if not partnerId.vat:
            raise ValidationError("No se declaró el número de documento para el contacto %s" % partnerId.name)
        if partnerId.l10n_latam_identification_type_id.l10n_avatar_py_code == 99:
            gDatRec.update({ 'iTiContRec': 1 if not partnerId.is_company else 2})
            gDatRec.update({ 'dRucRec': partnerId.vat.split('-')[0]})
            gDatRec.update({ 'dDVRec': partnerId.vat.split('-')[1]})
            gDatRec.update({ 'dNomRec': move.partner_id.name})
        else:
            gDatRec.update({ 'iTipIDRec': int(partnerId.l10n_latam_identification_type_id.l10n_avatar_py_code)})
            gDatRec.update({ 'dDTipIDRec': partnerId.l10n_latam_identification_type_id.name})
            if partnerId.l10n_latam_identification_type_id.l10n_avatar_py_code == 5:
                gDatRec.update({ 'dNumIDRec': '0'})
                gDatRec.update({ 'dNomRec': 'Sin Nombre'})
            else:
                gDatRec.update({ 'dNumIDRec': partnerId.vat})
                gDatRec.update({ 'dNomRec': move.partner_id.name})
        if not partnerId.street and is_afa:
            raise ValidationError("Falta definir al calle para el contacto %s" % partnerId.name)
        if partnerId.street:
            gDatRec.update({ 'dDirRec': partnerId.street})
            gDatRec.update({ 'dNumCasRec': partnerId.external_number if partnerId.external_number else 0})
            if not is_afa:
                gDatRec.update({ 'cDepRec': partnerId.state_id.code})
                gDatRec.update({ 'dDesDepRec': partnerId.state_id.name})
                if not partnerId.city_id:
                    raise ValidationError("Falta definir la ciudad para el contacto %s" % partnerId.name)
                gDatRec.update({ 'cCiuRec': partnerId.city_id.code})
                gDatRec.update({ 'dDesCiuRec': partnerId.city_id.name})
        if partnerId.municipality_id:
            gDatRec.update({ 'cDisRec': partnerId.municipality_id.code})
            gDatRec.update({ 'dDesDisRec': partnerId.municipality_id.name})
        if partnerId.phone:
            gDatRec.update({ 'dTelRec': partnerId.phone})
        if partnerId.mobile:
            gDatRec.update({ 'dCelRec': partnerId.mobile})
        if partnerId.email:
            gDatRec.update({ 'dEmailRec': partnerId.email})

        if xmlgen:
            rec_xmlgen = {}
            rec_xmlgen.update({ 'contribuyente': True if gDatRec['iNatRec'] == 1 else False})
            rec_xmlgen.update({ 'tipoOperacion': gDatRec['iTiOpe']})
            rec_xmlgen.update({ 'pais': gDatRec['cPaisRec']})
            if gDatRec.get('iTiContRec') != None:
                rec_xmlgen.update({ 'tipoContribuyente': gDatRec['iTiContRec']})
            if gDatRec.get('dRucRec') != None:
                rec_xmlgen.update({ 'ruc': str(gDatRec['dRucRec']) + '-' + str(gDatRec['dDVRec'])})
            if gDatRec.get('iTipIDRec') != None:
                rec_xmlgen.update({ 'documentoTipo': gDatRec['iTipIDRec']})
            if gDatRec.get('dNumIDRec') != None:
                rec_xmlgen.update({ 'documentoNumero': gDatRec['dNumIDRec']})
            rec_xmlgen.update({ 'razonSocial': gDatRec['dNomRec']})
            if gDatRec.get('dDirRec') != None:
                rec_xmlgen.update({ 'direccion': gDatRec['dDirRec']})
            if gDatRec.get('dNumCasRec') != None:
                rec_xmlgen.update({ 'numeroCasa': gDatRec['dNumCasRec']})
            if gDatRec.get('cDepRec') != None:
                rec_xmlgen.update({ 'departamento': gDatRec['cDepRec']})
            if gDatRec.get('cDisRec') != None:
                rec_xmlgen.update({ 'distrito': gDatRec['cDisRec']})
            if gDatRec.get('cCiuRec') != None:
                rec_xmlgen.update({ 'ciudad': gDatRec['cCiuRec']})
            if gDatRec.get('dTelRec') != None:
                rec_xmlgen.update({ 'telefono': gDatRec['dTelRec']})
            if gDatRec.get('dCelRec') != None:
                rec_xmlgen.update({ 'celular': gDatRec['dCelRec']})
            if gDatRec.get('dEmailRec') != None:
                rec_xmlgen.update({ 'email': gDatRec['dEmailRec']})
            return rec_xmlgen
        return gDatRec

    # E Campos específicos por tipo de Documento Electrónico (E001-E009)
        """
			'gDtipDE': {        // E001
			    'gCamFE': {},   // E010
				'gCamAE': {},   // E300
				'gCamNCDE': {}, // E400
				'gCamNRE': {},  // E500
				'gCamCond': {}, // E600
				'gCamItem': [], // E700
				'gCamEsp': {},  // E790
				'gTransp': {},  // E900
			},
        """

    # E1 Campos que componen la Factura Electrónica FE (E002-E099)
    def _get_sifen_gCamFE( self, move:AccountMove, xmlgen=False):
        """
			    'gCamFE': {              // E010    "factura" : {
				    'iIndPres': 'N',     // E011        "presencia" : 1,
					'dDesIndPres': 'A',  // E012
					'dFecEmNR': 'F',     // E013        "fechaEnvio" : "2023-10-21",
					'gCompPub': {},      // E020        "dncp" : {},
				},                                  },
        """
        gCamFE = {}
        rec_xmlgen = {}
        gCamFE.update({ 'iIndPres': 1})
        gCamFE.update({ 'dDesIndPres': 'Operación presencial'})
        if xmlgen:
            rec_xmlgen.update({ 'presencia': 1})
            rec_xmlgen.update({ 'dncp': self._get_sifen_gCompPub(move,xmlgen)})
            return rec_xmlgen
        else:
            gCamFE.update({ 'gCompPub': self._get_sifen_gCompPub(move,xmlgen)})
        return gCamFE

    # E1.1 Campos de informaciones de Compras Públicas (E020-E029)
    def _get_sifen_gCompPub( self, move:AccountMove, xmlgen=False):
        """
					'gCompPub': {          // E020    "dncp" : {
					    'dModCont': 'A',   // E021        "modalidad" : "ABC",
						'dEntCont': 'N',   // E022        "entidad" : 1,
						'dAnoCont': 'N',   // E023        "año" : 2021,
						'dSecCont': 'N',   // E024        "secuencia" : 3377,
						'dFeCodCont': 'F', // E025        "fecha" : "2022-09-14T10:11:00",
					},                                },
        """
        gCompPub = {}
        return gCompPub

    # E4 Campos que componen la Autofactura Electrónica AFE (E300-E399)
    def _get_sifen_gCamAE( self, partner:Partner, journal:AccountJournal, xmlgen=False):
        """
				'gCamAE': {             // E300    "autoFactura" : {
				    'iNatVen': 'N',     // E301        "tipoVendedor" : 1,
					'dDesNatVen': 'A',  // E302
					'iTipIDVen'; 'N',   // E304        "documentoTipo" : 1,
					'dDTipIDVen': 'A',  // E305
					'dNumIDVen': 'A',   // E306        "documentoNumero" : 1,
					'dNomVen': 'A',     // E307        "nombre" : "Vendedor autofactura",
					'dDirVen': 'A',     // E308        "direccion" : "Vendedor autofactura",
					'dNumCasVen': 'N',  // E309        "numeroCasa" : "Vendedor autofactura",
					'cDepVen': 'N',     // E310        "departamento" : 11,
					'dDesDepVen': 'A',  // E311
					'cDisVen': 'N',     // E312        "distrito" : 143,
					'dDesDisVen': 'A',  // E313
					'cCiuVen': 'N',     // E314        "ciudad" : 3344,
					'dDesCiuVen': 'A',  // E315
                                                       "transaccion" : {
					'dDirProv': 'A',    // E316            "lugar" : "Donde se realiza la transaccion",
					'cDepProv': 'N',    // E317            "departamento" : 11,
					'dDesDepProv': 'A', // E318
					'cDisProv'; 'N',    // E319            "distrito" : 143,
					'dDesDisProv': 'A', // E320
					'cCiuProv'; 'N',    // E321            "ciudad" : 3344,
					'dDesCiuProv': 'A', // E322
                                                       },
				},                                 },
        """
        gCamAE = {}
        rec_xmlgen = {}
        if not partner.country_id:
            partner.country_id = self.env['res.country'].search([('code', '=', 'PY')])
        if partner.country_id.code == 'PY':
            gCamAE.update({ 'iNatVen': 1})
            gCamAE.update({ 'dDesNatVen': 'No contribuyente'})
        else:
            gCamAE.update({ 'iNatVen': 2})
            gCamAE.update({ 'dDesNatVen': 'Extranjero'})
        if not partner.l10n_latam_identification_type_id:
            raise ValidationError("El contacto %s no tiene declarado el tipo de documento" % partner.name)
        gCamAE.update({ 'iTipIDVen': partner.l10n_latam_identification_type_id.l10n_avatar_py_code})
        gCamAE.update({ 'dDTipIDVen': partner.l10n_latam_identification_type_id.name})
        if not partner.vat:
            raise ValidationError("El contacto %s no tiene declarado el número de documento" % partner.name)
        gCamAE.update({ 'dNumIDVen': partner.vat})
        gCamAE.update({ 'dNomVen': partner.name})
        addressId = partner
        if partner.country_code != 'PY':
            addressId = journal.l10n_ar_afip_pos_partner_id
        if not addressId.street:
            raise ValidationError("El contacto %s no tiene declarado la calle en su dirección" % partner.name)
        gCamAE.update({ 'dDirVen': addressId.street})
        gCamAE.update({ 'dNumCasVen': addressId.external_number if addressId.external_number else 0})
        if not addressId.state_id:
            raise ValidationError("El contacto %s no tiene declarado el departamento en su dirección" % partner.name)
        gCamAE.update({ 'cDepVen': addressId.state_id.code})
        gCamAE.update({ 'dDesDepVen': addressId.state_id.name})
        if addressId.municipality_id:
            gCamAE.update({ 'cDisVen': addressId.municipality_id.code})
            gCamAE.update({ 'dDesDisVen': addressId.municipality_id.name})
        if not addressId.city_id:
            raise ValidationError("El contacto %s no tiene declarado la ciudad en su dirección" % partner.name)
        gCamAE.update({ 'cCiuVen': addressId.city_id.code})
        gCamAE.update({ 'dDesCiuVen': addressId.city_id.name})
        addressId = journal.l10n_ar_afip_pos_partner_id
        gCamAE.update({ 'dDirProv': addressId.street})
        gCamAE.update({ 'cDepProv': addressId.state_id.code})
        gCamAE.update({ 'dDesDepProv': addressId.state_id.name})
        gCamAE.update({ 'cDisProv': addressId.municipality_id.code})
        gCamAE.update({ 'dDesDisProv': addressId.municipality_id.name})
        gCamAE.update({ 'cCiuProv': addressId.city_id.code})
        gCamAE.update({ 'dDesCiuProv': addressId.city_id.name})

        if xmlgen:
            rec_xmlgen.update({ 'tipoVendedor': gCamAE['iNatVen']})
            rec_xmlgen.update({ 'documentoTipo': gCamAE['iTipIDVen']})
            rec_xmlgen.update({ 'documentoNumero': gCamAE['dNumIDVen']})
            rec_xmlgen.update({ 'nombre': gCamAE['dNomVen']})
            rec_xmlgen.update({ 'direccion': gCamAE['dDirVen']})
            rec_xmlgen.update({ 'numeroCasa': gCamAE['dNumCasVen']})
            rec_xmlgen.update({ 'departamento': gCamAE['cDepVen']})
            if gCamAE.get('cDisVen') != None:
                rec_xmlgen.update({ 'distrito': gCamAE['cDisVen']})
            rec_xmlgen.update({ 'ciudad': gCamAE['cCiuVen']})
            transaccion = {}
            transaccion.update({ 'lugar': gCamAE['dDirProv']})
            transaccion.update({ 'departamento': gCamAE['cDepProv']})
            transaccion.update({ 'distrito': gCamAE['cDisProv']})
            transaccion.update({ 'ciudad': gCamAE['cCiuProv']})
            rec_xmlgen.update({ 'transaccion': transaccion})
            return rec_xmlgen
        return gCamAE

    # E5 Campos que componen la Nota de Crédito/Débito Electrónica NCE-NDE (E400-E499)
    def _get_sifen_gCamNCDE( self, move:AccountMove, xmlgen=False):
        """
				'gCamNCDE': {          // E400    "notaCreditoDebito" : {
				    'iMotEmi': 'N',    // E401        "motivo" : 1,
					'dDesMotEmi': 'A', // E402
				},                                },
        """
        gCamNCDE = {}
        if xmlgen:
            gCamNCDE.update({'motivo' : 1})
            return gCamNCDE
        gCamNCDE.update({'iMotEmi' : 1})
        gCamNCDE.update({'dDesMotEmi' : 'Devolución y Ajuste de precios'})
        return gCamNCDE

    # E6 Campos que componen la Nota de Remisión Electrónica (E500-E599)
    def _get_sifen_gCamNRE(self):
        """
				'gCamNRE': {              // E500    "remision" : {
				    'iMotEmiNR': 'N',     // E501        "motivo" : 1,
					'dDesMotEmiNR': 'A',  // E502
					'iRespEmiNR': 'N',    // E503        "tipoResponsable" : 1,
					'dDesRespEmiNR': 'A', // E504
					'dKmR': 'N',          // E505        "kms" : 150,
					'dFecEm': 'F',        // E506        "fechaFactura" : "2022-08-21",
				},                                   },
        """
        gCamNRE = {}
        return gCamNRE

    # E7 Campos que describen la condición de la operación (E600-E699)
    def _get_sifen_gCamCond(self, move:AccountMove, xmlgen=False):
        """
				'gCamCond': {         // E600    "condicion" : {
				    'iCondOpe': 'N',  // E601        "tipo" : 1,
					'dDCondOpe': 'A', // E602
					'gPaConEIni': [], // E605        "entregas" : [],
					'gPagCred': {},   // E640        "credito" : {),
				},                               },
        """
        gCamCond = {}
        rec_xmlgen = {}
        if move.invoice_date_due and (move.invoice_date_due - (move.invoice_date or datetime.now())).days > 15:
            gCamCond.update({ 'iCondOpe': 2})
            gCamCond.update({ 'dDCondOpe': 'Crédito'})
            if xmlgen:
                rec_xmlgen.update({ 'tipo': 2})
                rec_xmlgen.update({ 'credito': self._get_sifen_gPagCred( move, xmlgen)})
                return rec_xmlgen
            else:
                gCamCond.update({ 'gPagCred': self._get_sifen_gPagCred(move, xmlgen)})
            
        else:
            gCamCond.update({ 'iCondOpe': 1})
            gCamCond.update({ 'dDCondOpe': 'Contado'})
            if xmlgen:
                rec_xmlgen.update({ 'tipo': 1})
                rec_xmlgen.update({ 'entregas': self._get_sifen_gPaConEIni( move, xmlgen)})
                return rec_xmlgen
            else:
                gCamCond.update({ 'gPaConEIni': self._get_sifen_gPaConEIni(move)})
        return gCamCond

    # E7.1 Campos que describen la forma de pago de la operación al contado o del monto de la entrega inicial (E605-E619)
    def _get_sifen_gPaConEIni(self, move:AccountMove, xmlgen=False):
        """
					'gPaConEIni': [             // E605    "entregas" : [
					    {                                      {
						    'iTiPago': 'N',     // E606             "tipo" : 1,
							'dDesTiPag': 'A',   // E607
							'dMonTiPag': 'N',   // E608             "monto" : "150000",
							'cMoneTiPag': 'A',  // E609             "moneda" : "PYG",
							'dDMoneTiPag': 'A', // E610
							'dTiCamTiPag': 'N', // E611             "cambio" : 0
						    'gPagTarCD': {},    // E620             "infoTarjeta" : {},
						    'gPagCheq': {},     // E630             "infoCheque" : {},
						},                                     },
					],                                     ],
        """
        gPaConEIni = {}
        rec_xmlgen = {}
        gPaConEInis = []
        gPaConEIni.update({ 'iTiPago': 1}) # Forzamos a pago efectivo
        gPaConEIni.update({ 'dDesTiPag': 'Efectivo'})
        gPaConEIni.update({ 'dMonTiPag': move.amount_total})
        gPaConEIni.update({ 'cMoneTiPag': move.currency_id.name})
        gPaConEIni.update({ 'dDMoneTiPag': move.currency_id.full_name})
        if move.currency_id.name != 'PYG':
            gPaConEIni.update({ 'dTiCamTiPag': round(1 / move.invoice_currency_rate, 2)})
        if xmlgen:
            rec_xmlgen.update({ 'tipo': gPaConEIni['iTiPago']})
            rec_xmlgen.update({ 'monto': gPaConEIni['dMonTiPag']})
            rec_xmlgen.update({ 'moneda': gPaConEIni['cMoneTiPag']})
            if gPaConEIni.get('dTiCamTiPag') != None:
                rec_xmlgen.update({ 'cambio': gPaConEIni['dTiCamTiPag']})
            gPaConEInis.append(rec_xmlgen)
            return gPaConEInis
        gPaConEInis.append(gPaConEIni)
        return gPaConEInis

    # E7.1.1 Campos que describen el pago o entrega inicial de la operación con tarjeta de crédito/débito
    def _get_sifen_gPagTarCD( self, move:AccountMove, xmlgen=False):
        """
						'gPagTarCD': {          // E620    "infoTarjeta" : {
						    'iDenTarj': 'N',    // E621        "tipo" : 1,
							'dDesDenTarj': 'A', // E622        "tipoDescripcion" : "Dinelco",
							'dRSProTar': 'A',   // E623        "razonSocial" : "Bancard",
							'dRUCProTar': 'A',  // E624        "ruc" : "6969549654-1".split('-')[0],
							'dDVProTar': 'N',   // E625        "ruc" : "6969549654-1".split('-')[1],
							'iForProPa': 'N',   // E626        "medioPago" : 1,
							'dCodAuOpe': 'N',   // E627        "codigoAutorizacion" : 232524234
							'dNomTit': 'A',     // E628
							'dNumTarj': 'N',    // E629        "titular" : "Marcos Jara"
						},                                 },
        """
        gPagTarCD = {}
        return gPagTarCD

    # E7.1.2 Campos que describen el pago o entrega inicial de la operación con cheque (E630-E639)
    def _get_sifen_gPagCheq( self, move:AccountMove, xmlgen=False):
        """
						'gPagCheq': {        // E630    "infoCheque" : {
						    'dNumCheq': 'N', // E631        "numeroCheque": "32323232",
							'dBcoEmi': 'A',  // E632        "banco" : "Sudameris",
						},                              },
        """
        gPagCheq = {}
        return gPagCheq

    # E7.2 Campos que describen la operación a crédito (E640-E649)
    def _get_sifen_gPagCred(self, move:AccountMove, xmlgen=False):
        """
					'gPagCred': {          // E640    "credito" : {
					    'iCondCred': 'N',  // E641        "tipo" : 1,
						'dDCondCred': 'A', // E642
						'dPlazoCre': 'A',  // E643        "plazo" : "30 días",
						'dCuotas': 'N',    // E644        "cuotas" : 2,
						'dMonEnt': 'N',    // E645        "montoEntrega" : 1500000.00,
						'gCuotas': [].     // E650        "infoCuotas" : [],   _get_sifen_gCuotas
					},                                },
        """
        gPagCred = {}
        rec_xmlgen = {}
        gCuotas = []
        if move.invoice_payment_term_id:
            gCuotas = self._get_sifen_gCuotas(move, xmlgen)
            if len(gCuotas) > 1:
                gPagCred.update({ 'iCondCred': 2}) #Cuotas
                gPagCred.update({ 'dDCondCred': 'Cuota'})
                gPagCred.update({ 'dCuotas': len(gCuotas)})
                gPagCred.update({ 'gCuotas': gCuotas})
            else:
                gPagCred.update({ 'iCondCred': 1}) #Plazo
                gPagCred.update({ 'dDCondCred': 'Plazo'})
                gPagCred.update({ 'dPlazoCre': 
                    str(round((move.invoice_date_due - (move.invoice_date or datetime.now())).days,0)) + " días" })
        else: # Plazo
            gPagCred.update({ 'iCondCred': 1}) #Plazo
            gPagCred.update({ 'dDCondCred': 'Plazo'})
            gPagCred.update({ 'dPlazoCre': 
                str(round((move.invoice_date_due - (move.invoice_date or datetime.now())).days,0)) + " días" })
        if xmlgen:
            iCondCred = gPagCred['iCondCred']
            rec_xmlgen.update({ 'tipo':  iCondCred})
            if iCondCred == 1:
                rec_xmlgen.update({ 'cuotas':  len(gCuotas)})
                rec_xmlgen.update({ 'infoCuotas':  gCuotas})
            else:
                rec_xmlgen.update({ 'plazo':  gPagCred['dPlazoCre']})
            return rec_xmlgen
        return gPagCred

    # E7.2.1 Campos que describen las cuotas (E650-E659)
    def _get_sifen_gCuotas(self, move:AccountMove, xmlgen=False):
        """
						'gCuotas': [              // E650    "infoCuotas" : [
						    {                                    {
							    'cMoneCuo': 'A',  // E653            "moneda" : "PYG",
								'dDMoneCuo': 'A', // E654
								'dMonCuota': 'N', // E651            "monto" : 800000.00,
								'dVencCuo': 'F',  // E652            "vencimiento" : "2021-10-30",
							},                                   },
						].                                   ],
        """
        gCuotas = []
        sign = 1 if move.is_inbound(include_receipts=True) else -1
        invoice_payment_terms = move.invoice_payment_term_id._compute_terms(
                        date_ref=move.invoice_date or move.date or fields.Date.context_today(self),
                        currency=move.currency_id,
                        tax_amount_currency=move.amount_tax * sign,
                        tax_amount=move.amount_tax_signed,
                        untaxed_amount_currency=move.amount_untaxed * sign,
                        untaxed_amount=move.amount_untaxed_signed,
                        company=move.company_id,
                        cash_rounding=move.invoice_cash_rounding_id,
                        sign=sign
                    )
        for line in invoice_payment_terms['line_ids']:
            gCuota = {}
            rec_xmlgen = {}
            gCuota.update({ 'cMoneCuo': move.currency_id.name})
            gCuota.update({ 'dDMoneCuo': move.currency_id.full_name})
            gCuota.update({ 'dMonCuota': line.get('foreign_amount')})
            gCuota.update({ 'dVencCuo': line.get('date').strftime("%Y-%m-%d")})
            if xmlgen:
                rec_xmlgen.update({ 'moneda': gCuota['cMoneCuo']})
                rec_xmlgen.update({ 'monto': gCuota['dMonCuota']})
                rec_xmlgen.update({ 'vencimiento': gCuota['dVencCuo']})
                gCuotas.append( rec_xmlgen)
            else:
                gCuotas.append( gCuota)
        return gCuotas

    # E8 Campos que describen los ítems de la operación (E700-E899)
    def _get_sifen_gCamItem( self, item:AccountMoveLine, xmlgen=False):
        """
				'gCamItem': [                 // E700    "items" : [{
				    {
					    'dCodInt': 'A',       // E701        "codigo" : "A-001",
						'dParAranc': 'N',     // E702        "partidaArancelaria" : 4444,
						'dNCM': 'N'           // E703        "ncm": "ABCD1234",
                                                             "dncp" : {
						'dDncpG': 'A',        // E704            "codigoNivelGeneral" : "12345678",
						'dDncpE': 'A',        // E705            "codigoNivelEspecifico" : "1234",
						'dGtin': 'N',         // E706            "codigoGtinProducto" : "12345678",
						'dGtinPq': 'N',       // E707            "codigoNivelPaquete" : "12345678"
                                                            },
						'dDesProSer': 'A',    // E708       "descripcion": "Producto o Servicio", 
						'cUniMed': 'N',       // E709       "unidadMedida": 77,
						'dDesUniMed': 'A',    // E710
						'dCantProSer': 'N',   // E711       "cantidad": 10.5,
						'cPaisOrig': 'A',     // E712       "pais" : "PRY",
						'dDesPaisOrig': 'A',  // E713
						'dInfItem': 'A',      // E714
						'cRelMerc': 'N',      // E715
						'dDesRelMerc': 'A',   // E716
						'dCanQuiMer': 'N',    // E717
						'dPorQuiMer': 'N',    // E718
						'dCDCAnticipo': 'A',  // E719
						'gValorItem': {},     // E720        _get_sifen_gValorItem
						'gCamIVA': {},        // E730
						'gRasMerc': {},       // E750
						'gVehNuevo': {},      // E770
					},
				],                                       }],
        """
        gCamItem = {}
        rec_xmlgen = {}
        productId = item.product_id
        gCamItem.update({ 'dCodInt': productId.default_code if productId.default_code else str(item.id) }) #E701
        gCamItem.update({ 'dDesProSer': item.name}) # E711
        gCamItem.update({ 'cUniMed': item.product_uom_id.l10n_avatar_py_code}) # E709
        gCamItem.update({ 'dDesUniMed': item.product_uom_id.l10n_avatar_py_description}) # E710
        gCamItem.update({ 'dCantProSer': item.quantity}) # E711
        
        if xmlgen:
            rec_xmlgen.update({'codigo': gCamItem['dCodInt']})
            rec_xmlgen.update({'descripcion': gCamItem['dDesProSer']})
            rec_xmlgen.update({'unidadMedida': gCamItem['cUniMed']})
            rec_xmlgen.update({'cantidad': gCamItem['dCantProSer']})
            rec_xmlgen.update(  self._get_sifen_gValorItem( item, True))
            rec_xmlgen.update(  self._get_sifen_gCamIVA( item, True))
            return rec_xmlgen
        else:
            gCamItem.update({ 'gValorItem': self._get_sifen_gValorItem( item)}) # E720
            gCamItem.update({ 'gCamIVA': self._get_sifen_gCamIVA( item)})

        return gCamItem

    # E8.1 Campos que describen el precio, tipo de cambio y valor total de la operación por ítem (E720-E729)
    def _get_sifen_gValorItem( self, item:AccountMoveLine, xmlgen=False):
        """
						'gValorItem': {             // E720    "items" : [{
						    'dPUniProSer': 'N',     // E721        "precioUnitario": 10800,
							'dTiCamIt': 'N',        // E725        "cambio": 0,
							'dTotBruOpeItem': 'N',  // E727
							'gValorRestaItem': {},  // EA001
						},                                     }],
        """
        gValorItem = {}
        rec_xmlgen = {}
        gValorItem.update({ 'dPUniProSer': item.price_unit })
        gValorItem.update({ 'dTotBruOpeItem': item.quantity * item.price_unit })
        
        if xmlgen:
            rec_xmlgen.update({ 'precioUnitario': gValorItem['dPUniProSer']})
            rec_xmlgen.update( self._get_sifen_gValorRestaItem(item,True))
            return rec_xmlgen
        else:
            gValorItem.update({ 'gValorRestaItem': self._get_sifen_gValorRestaItem(item) })
        return gValorItem

    # E8.1.1 Campos que describen los descuentos, anticipos y valor total por ítem (EA001-EA050)
    def _get_sifen_gValorRestaItem( self, item:AccountMoveLine, xmlgen=False):
        """
							'gValorRestaItem': {        // EA001    "items" : [{
							    'dDescItem': 'N',       // EA002        "descuento": 0,
								'dPorcDesIt': 'N',      // EA003
								'dDescGloItem': 'N',    // EA004
								'dAntPreUniIt': 'N',    // EA006
								'dAntGloPreUniIt': 'N', // EA007
								'dTotOpeItem': 'N',     // EA008
								'dTotOpeGs': 'N',       // EA009
							},                                      }],
        """
        gValorRestaItem = {}
        rec_xmlgen = {}
        if item.discount > 0.0:
            gValorRestaItem.update({ 'dPorcDesIt': item.discount}) # EA003
            gValorRestaItem.update({ 'dDescItem': round(( item.quantity * item.price_unit ) * item.discount / 100.0, )})
            rec_xmlgen.update({ 'descuento': gValorRestaItem['dDescItem']})
        gValorRestaItem.update({ 'dTotOpeItem': item.price_total }) # EA008
        if item.company_currency_id != item.currency_id:
            gValorRestaItem.update({ 'dTotOpeItem': round(item.price_total / item.move_id.invoice_currency_rate, 2)})
        if xmlgen:
            return rec_xmlgen
        return gValorRestaItem

    # E8.2 Campos que describen el IVA de la operación por ítem (E730-E739)
    def _get_sifen_gCamIVA( self, item:AccountMoveLine, xmlgen=False):
        """
						'gCamIVA': {            // E730    "items" : [{
						    'iAfecIVA': 'N',    // E731        "ivaTipo" : 1,
							'dDesAfecIVA': 'A', // E732
							'dPropIVA': 'N',    // E733        "ivaBase" : 100,
							'dTasaIVA': 'N',    // E734        "iva" : 5,
							'dBasGravIVA': 'N', // E735
							'dLiqIVAItem': 'N', // E736
						},                                  }],
        """
        gCamIVA = {}
        rec_xmlgen = {}
        for tax in item.tax_ids:
            gCamIVA.update({ 'iAfecIVA': int(tax.l10n_avatar_py_tax_assessment)}) # E731
            if tax.l10n_avatar_py_tax_assessment == '1':
                gCamIVA.update({ 'dDesAfecIVA': 'Gravado IVA'}) # E732
            elif tax.l10n_avatar_py_tax_assessment == '2':
                gCamIVA.update({ 'dDesAfecIVA': 'Exonerado (Art. 83- Ley 125/91)'}) # E732
            elif tax.l10n_avatar_py_tax_assessment == '3':
                gCamIVA.update({ 'dDesAfecIVA': 'Exento”'}) # E732
            elif tax.l10n_avatar_py_tax_assessment == '4':
                gCamIVA.update({ 'dDesAfecIVA': 'Gravado parcial (Grav- Exento)'}) # E732
            gCamIVA.update({ 'dPropIVA': int(tax.l10n_avatar_py_base_tax)}) # E733
            if gCamIVA.get('iAfecIVA') in (1,4):
                gCamIVA.update({ 'dTasaIVA': int(tax.tax_group_id.l10n_avatar_py_tax_type)}) # E734
                dTasaIVA_E734_f = float(gCamIVA.get('dTasaIVA') or 10.0)
                dPropIVA_E733_f = float(gCamIVA.get('dPropIVA') or 100.0)
                dBasGravIVA_E735 = ( 100.0 * item.price_total * dPropIVA_E733_f) / ( 10000.0 + ( dTasaIVA_E734_f * dPropIVA_E733_f))
                gCamIVA.update({ 'dBasGravIVA': dBasGravIVA_E735}) # E735
                gCamIVA.update({ 'dLiqIVAItem': dBasGravIVA_E735 * dTasaIVA_E734_f / 100.0}) # E736
            else:
                gCamIVA.update({ 'dTasaIVA': 0}) # E734
                gCamIVA.update({ 'dBasGravIVA': 0}) # E735
                gCamIVA.update({ 'dLiqIVAItem': 0}) # E736
            if xmlgen:
                rec_xmlgen.update({ 'ivaTipo': gCamIVA.get('iAfecIVA')})
                rec_xmlgen.update({ 'ivaBase': gCamIVA.get('dPropIVA')})
                rec_xmlgen.update({ 'iva': gCamIVA.get('dTasaIVA')})
        if xmlgen:
            return rec_xmlgen
        return gCamIVA

    # E8.4 Grupo de rastreo de la mercadería (E750-E760)
    def _get_sifen_gRasMerc( self, item:AccountMoveLine, xmlgen=False):
        """
						'gRasMerc': {             // E750    "items" : [{
						    'dNumLote': 'A',      // E751        "lote" : "A-001",
							'dVencMerc': 'F',     // E752        "vencimiento" : "2022-10-30",
							'dNSerie': 'A',       // E753        "numeroSerie" : "",
							'dNumPedi': 'A',      // E754        "numeroPedido" : "",
							'dNumSegui': 'A',     // E755        "numeroSeguimiento" : "",
							'dNomImp': 'A',       // E756 Eliminado por la NT 009
							'dDirImp': 'A',       // E757 Eliminado por la NT 009
							'dNumFir': 'A',       // E758 Eliminado por la NT 009
							'dNumReg': 'A',       // E759        "registroSenave" : "323223",
							'dNumRegEntCom': 'A', // E760        "registroEntidadComercial" : "RI-32/22",
						},                                   }],
        """
        gRasMerc = {}
        return gRasMerc

    # E8.5 Sector de automotores nuevos y usados (E770-E789)
    def _get_sifen_gVehNuevo( self, item:AccountMoveLine, xmlgen=False):
        """
						'gVehNuevo': {           // E770    "sectorAutomotor" : {
						    'iTipOpVN': 'N',     // E771        "tipo" : 1,
							'dDesTipOpVN': 'A',  // E772
							'dChasis': 'A',      // E773        "chasis" : "45252345235423532",
							'dColor': 'A',       // E774        "color" : "Rojo",
							'dPotencia': 'N',    // E775        "potencia" : 1500,
							'dCapMot': 'N',      // E776        "capacidadMotor" : 5,
							'dPNet': 'N',        // E777        "pesoNeto" : 8000,
							'dPBruto': 'N',      // E778        "pesoBruto" : 10000,
							'iTipCom': 'N',      // E779        "tipoCombustible" : 9,
							'dDesTipCom': 'A',   // E780
							'dNroMotor': 'A',    // E781        "numeroMotor" : "323234234234234234",
							'dCapTracc': 'N',    // E782        "capacidadTraccion" : 151.01,
							'dAnoFab': 'N',      // E783        "año" : 2009,
							'cTipVeh': 'A',      // E784        "tipoVehiculo" : "Camioneta",
							'dCapac': 'N',       // E785        "capacidadPasajeros" : 5,
							'dCilin': 'A',       // E786        "cilindradas" : "3500",
						},                                  },
        """
        gVehNuevo = {}
        return gVehNuevo

    # E9 Campos complementarios comerciales de uso específico (E790-E899)
    def _get_sifen_gCamEsp( self, xmlgen=False):
        """
				'gCamEsp': {         // E790
				    'gGrupEner': {}, // E791
					'gGrupSeg': {},  // E800
					'gGrupSup': {},  // E810
					'gGrupAdi': {},  // E820
				}, 
        """
        gCamEsp = {}
        return gCamEsp
    # E9.2 Sector Energía Eléctrica (E791-E799)
    def _get_sifen_gGrupEner( self, xmlgen=False):
        """
				    'gGrupEner': {       // E791    "sectorEnergiaElectrica" : {
					    'dNroMed': 'A',  // E792        "numeroMedidor" : "132423424235425",
						'dActiv': 'N',   // E793        "codigoActividad" : 125,
						'dCateg': 'A',   // E794        "codigoCategoria" : "001",
						'dLecAnt': 'N',  // E795        "lecturaAnterior" : 4,
						'dLecAct': 'N',  // E796        "lecturaActual" : 5,
						'dConKwh': 'N',  // E797
					},                              },
        """
        gGrupEner = {}
        return gGrupEner

    # E9.3 Sector de Seguros (E800-E809)
    def _get_sifen_gGrupSeg( self, xmlgen=False):
        """
					'gGrupSeg': {          // E800    "sectorSeguros" : {
					    'dCodEmpSeg': 'A', // E801        "codigoAseguradora" : "",
						'gGrupPolSeg': [], // EA790       {}, // _get_sifen_gGrupPolSeg
					},                                },
        """
        gGrupSeg = {}
        return gGrupSeg

    # E9.3.1 Póliza de seguros (EA790-EA799)
    def _get_sifen_gGrupPolSeg( self, xmlgen=False):
        """
						'gGrupPolSeg'; [            // EA790    "sectorSeguros" : {
                            {
						        'dPoliza': 'A',     // EA791        "codigoPoliza" : "AAAA",
							    'dUnidVig': 'A',    // EA792        "vigenciaUnidad" : "año",
							    'dVigencia': 'N',   // EA793        "vigencia" : 1,
							    'dNumPoliza': 'A',  // EA794        "numeroPoliza" : "BBBB",
							    'dFecIniVig': 'F',  // EA795        "inicioVigencia" : "2021-10-01",
							    'dFecFinVig': 'F',  // EA796        "finVigencia" : "2022-10-01",
							    'dCodInt': 'A',     // EA797        "codigoInternoItem" : "A-001"
                            }
						],                                      },
        """
        gGrupPolSeg = []
        return gGrupPolSeg
    # E9.4 Sector de Supermercados (E810-E819)
    def _get_sifen_gGrupSup( self, xmlgen=False):
        """
					'gGrupSup': {          // E810    "sectorSupermercados" : {
					    'dNomCaj': 'A',    // E811        "nombreCajero" : "Juan Antonio Caceres",
						'dEfectivo': 'N',  // E812        "efectivo" : 150000,
						'dVuelto': 'N',    // E813        "vuelto" : 30000,
						'dDonac': 'N',     // E814        "donacion" : 1000,
						'dDesDonac': 'A',  // E815        "donacionDescripcion" : "Donado para la caridad"
					},                                },
        """
        gGrupSup = {}
        return gGrupSup

    # E9.5 Grupo de datos adicionales de uso comercial (E820-E829)
    def _get_sifen_gGrupAdi( self, xmlgen=False):
        """
					'gGrupAdi': {         // E820    "sectorAdicional" : {
					    'dCiclo': 'A',    // E821        "ciclo" : "Mensualidad",
						'dFecIniC': 'F',  // E822        "inicioCiclo" : "2021-09-01",
						'dFecFinC': 'F',  // E823        "finCiclo" : "2021-10-01",
						'dVencPag': 'F',  // E824        "vencimientoPago" : "2021-11-01",
						'dContrato': 'A', // E825        "numeroContrato" : "AF-2541",
						'dSalAnt': 'N',   // E826        "saldoAnterior" : 1550000,
					},                               },
        """
        gGrupAdi = {}
        return gGrupAdi

    # E10 Campos que describen el transporte de las mercaderías (E900-E999)
    def _get_sifen_gTransp( self, xmlgen=False):
        """
				'gTransp': {              // E900    "detalleTransporte" : {
				    'iTipTrans': 'N',     // E901        "tipo" : 1,
					'dDesTipTrans': 'A',  // E902
					'iModTrans': 'N',     // E903        "modalidad" : 1,
					'dDesModTrans': 'A',  // E904
					'iRespFlete': 'N',    // E905        "tipoResponsable" : 1,
					'cCondNeg': 'A',      // E906        "condicionNegociacion" : "CFR",
					'dNuManif': 'A',      // E907        "numeroManifiesto" : "AF-2541",
					'dNuDespImp': 'A',    // E908        "numeroDespachoImportacion" : "153223232332",
					'dIniTras': 'F',      // E909        "inicioEstimadoTranslado" : "2021-11-01",
					'dFinTras': 'F',      // E910        "finEstimadoTranslado" : "2021-11-01",
					'cPaisDest': 'A',     // E911        "paisDestino" : "PRY", 
					'dDesPaisDest': 'A',  // E912
					'gCamSal': {},        // E920        "salida" : {},
					'gCamEnt': {},        // E940        "entrega" : {},
					'gVehTras': [],       // E960        "vehiculo" : [],
					'gCamTrans': {},      // E980        "transportista" : {},
				},                                   },
        """
        gTransp = {}
        return gTransp

    # E10.1 Campos que identifican el local de salida de las mercaderías (E920-E939)
    def _get_sifen_gCamSal( self, xmlgen=False):
        """
					'gCamSal': {            // E920    "salida" : {
					    'dDirLocSal': 'A',  // E921        "direccion" : "Paraguay",
						'dNumCasSal': 'N',  // E922        "numeroCasa" : "Paraguay",
						'dComp1Sal': 'A',   // E923        "complementoDireccion1" : "Entre calle 2", 
						'dComp2Sal': 'A',   // E924        "complementoDireccion2" : "y Calle 7",
						'cDepSal': 'N',     // E925        "departamento" : 11,
						'dDesDepSal': 'A',  // E926
						'cDisSal': 'N',     // E927        "distrito" : 143,
						'dDesDisSal': 'A',  // E928
						'cCiuSal': 'N',     // E929        "ciudad" : 3344,
						'dDesCiuSal': 'A',  // E930
						'dTelSal': 'A',     // E931        "telefonoContacto" : "097x",
					},                                 },
        """
        gCamSal = {}
        return gCamSal

    # E10.2 Campos que identifican el local de entrega de las mercaderías (E940-E959)
    def _get_sifen_gCamEnt( self, xmlgen=False):
        """
					'gCamEnt': {            // E940    "entrega" : {
					    'dDirLocEnt': 'A',  // E941        "direccion" : "Paraguay",
						'dNumCasEnt': 'N',  // E942        "numeroCasa" : "Paraguay",
						'dComp1Ent': 'A',   // E943        "complementoDireccion1" : "Entre calle 2", 
						'dComp2Ent': 'A',   // E944        "complementoDireccion2" : "y Calle 7",
						'cDepEnt': 'N',     // E945        "departamento" : 11,
						'dDesDepEnt': 'A',  // E946
						'cDisEnt': 'N',     // E947        "distrito" : 143,
						'dDesDisEnt': 'A',  // E948
						'cCiuEnt': 'N',     // E949        "ciudad" : 3344,
						'dDesCiuEnt': 'A',  // E950
						'dTelEnt': 'A',     // E951        "telefonoContacto" : "097x",
					},                                 }
        """
        gCamEnt = {}
        return gCamEnt

    # E10.3 Campos que identifican el vehículo de traslado de mercaderías (E960-E979)
    def _get_sifen_gVehTras( self, xnlgen=False):
        """
					'gVehTras': [                // E960    "vehiculo" : {
					    {
						    'dTiVehTras': 'A',   // E961        "tipo" : 1,
							'dMarVeh': 'A',      // E962        "marca" : "Nissan",
							'dTipIdenVeh': 'N',  // E967        "documentoTipo" : 1,
							'dNroIDVeh': 'A',    // E963        "documentoNumero" : "232323-1",
							'dAdicVeh': 'A',     // E964        "obs" : "",
							'dNroMatVeh': 'A',   // E965        "numeroMatricula" : "ALTO PARANA",
							'dNroVuelo': 'A',    // E966        "numeroVuelo" : 143,
						},
                    ],                                      },
        """
        gVehTras = {}
        return gVehTras
    # E10.4 Campos que identifican al transportista (persona física o jurídica) (E980-E999)
    def _get_sifen_gCamTrans( self, xmlgen=False):
        """
					'gCamTrans': {            // E980    "transportista" : {
					    'iNatTrans': 'N',     // E981        "contribuyente" : true,
						'dNomTrans': 'A',     // E982        "nombre" : "Paraguay",
						'dRucTrans': 'A',     // E983        "ruc" : "80068684-1".split('-')[0],
						'dDVTrans': 'N',      // E984        "ruc" : "80068684-1".split('-')[1],
						'iTipIDTrans': 'N',   // E985        "documentoTipo" : 1,
						'dDTipIDTrans': 'A',  // E986
						'dNumIDTrans': 'A',   // E987        "documentoNumero" : "99714584",
						'cNacTrans': 'A',     // E988        "pais" : "PRY",
						'dDesNacTrans': 'A',  // E989
                                                             "chofer": {
						'dNumIDChof': 'A',    // E990            "documentoNumero" : "",
						'dNomChof': 'A',      // E991            "nombre" : "Jose Benitez",
						'dDomFisc': 'A',      // E992            "direccion" : "Jose Benitez"
						'dDirChof': 'A',      // E993            "direccion" : "Jose Benitez"
                                                             },
                                                             "agente" : {
						'dNombAg': 'A',       // E994            "nombre" : "Jose Benitez",
						'dRucAg': 'A',        // E995            "ruc" : "515415-1".split('-')[0],
						'dDVAg': 'N',         // E996            "ruc" : "515415-1".split('-')[1],
						'dDirAge': 'A',       // E997            "direccion" : "Jose Benitez",
                                                            },
					},                                   },
        """
        gCamTrans = {}
        return gCamTrans

    # F Campos que describen los subtotales y totales de la transacción documentada (F001-F099)
    def _get_sifen_gTotSub( self):
        """
			'gTotSub': {                // F001
			    'dSubExe': 'N',         // F002
				'dSubExo': 'N',         // F003
				'dSub5': 'N',           // F004
				'dSub10': 'N',          // F005
				'dTotOpe': 'N',         // F008
				'dTotDesc': 'N',        // F009
				'dTotDescGlotem': 'N',  // F033
				'dTotAntItem': 'N',     // F034
				'dTotAnt': 'N',         // F035
				'dPorcDescTotal': 'N',  // F010
				'dDescTotal'; 'N',      // F011
				'dAnticipo'; 'N',       // F012
				'dRedon': 'N',          // F013
				'dComi': 'N',           // F025
				'dTotGralOpe': 'N',     // F014
				'dIVA5': 'N',           // F015
				'dIVA10': 'N',          // F016
				'dLiqTotIVA5': 'N',     // F036
				'dLiqTotIVA10': 'N',    // F037
				'dIVAComi': 'N',        // F026
				'dTotIVA': 'N',         // F017
				'dBaseGrav5': 'N',      // F018
				'dBaseGrav10': 'N',     // F019
				'dTBasGraIVA': 'N',     // F020
				'dTotalGs': 'N',        // F023
			},
        """
        gTotSub = {}
        return gTotSub

    # G Campos complementarios comerciales de uso general (G001-G049)
    def _get_sifen_gCamGen( self, xmlgen=False):
        """
			'gCamGen': {            // G001    "complementarios" : {
			    'dOrdCompra': 'A',  // G002        "ordenCompra" : "",
				'dOrdVta': 'A',     // G003        "ordenVenta" : "",
				'dAsiento': 'A',    // G004        "numeroAsiento" : "",
				'gCamCarg': {},     // G050        "carga": {},
			},                                 },
        """
        gCamGen = {}
        if xmlgen:
            gCamCarg = self._get_sifen_gCamCarg( xmlgen = True)
        else:
            gCamCarg = self._get_sifen_gCamCarg( xmlgen = False)
        if len(gCamCarg) > 0:
            gCamGen.update({ 'carga' if xmlgen else 'gCamCarg': gCamCarg})
        return gCamGen

    # G1 Campos generales de la carga (G050 - G099
    def _get_sifen_gCamCarg( self, xmlgen=False):
        """
				'gCamCarg': {                 // G050    "carga" : {
				    'cUniMedTotVol': 'N',     // G051       
					'dDesUniMedTotVol': 'A',  // G052       
					'dTotVolMerc': 'N',       // G053        
					'cUniMedTotPes': 'N',     // G054
					'dDesUniMedTotPes': 'A',  // G055
					'dTotPesMerc': 'N',       // G056
					'iCarCarga': 'N',         // G057
					'dDesCarCarga': 'A',      // G058
				},                                       },
        """
        gCamCarg = {}
        return gCamCarg

    # H Campos que identifican al documento asociado (H001-H049)
    def _get_sifen_gCamDEAsoc(self, move:AccountMove, xmlgen=False):
        """
			'gCamDEAsoc': [                // H001   "documentoAsociado" : [
			    {                                        {
				    'iTipDocAso': 'N',     // H002           "formato" : 1,
					'dDesTipDocAso': 'A',  // H003
					'dCdCDERef': 'A',      // H004           "cdc" : "01800695631001001000000612021112917595714694",
					'dNTimDI': 'N',        // H005           "timbrado" : "32323",
					'dEstDocAso': 'A',     // H006           "establecimiento" : "001",
					'dPExpDocAso': 'A',    // H007           "punto" : "001",
					'dNumDocAso': 'A',     // H008           "numero" : "00278211",
					'iTipoDocAso': 'N',    // H009           "tipo" : 1, o "tipoDocumentoImpreso"
					'dDTipoDocAso': 'A',   // H010
					'dFecEmiDI': 'F',      // H011           "fecha" : "2022-09-14",
					'dNumComRet': 'A',     // H012           "numeroRetencion" : "32323232",
					'dNumResCF': 'A',      // H013           "resolucionCreditoFiscal" : "32323",
					'iTipCons': 'N',       // H014           "constanciaTipo" : 1,
					'dDesTipCons': 'A',    // H015      
					'dNumCons': 'N',       // H016           "constanciaNumero" : 32323,
					'dNumControl': 'N',    // H017           "constanciaControl" : "33232323"
				},                                       },
			],                                       ],
        """
        gCamDEAsoc = []
        latamDocType = move.l10n_latam_document_type_id
        moveRev_ids = move.reversed_entry_id
        if latamDocType.internal_type == 'credit_note' and move.move_type == 'out_refund':
            moveRev_ids = move.reversed_entry_id
            iTiDE = 5 ## Nota de credito
            if not moveRev_ids:
                raise ValidationError( "La nota de crédito %s tiene que tener un documento asociado" % move.name)
        elif latamDocType.internal_type == 'debit_note' and move.move_type == 'out_invoice':
            moveRev_ids = move.debit_origin_id
            iTiDE = 6 ## Nota de debito
            if not moveRev_ids:
                raise ValidationError( "La nota de débito %s tiene que tener un documento asociado" % move.name)
        elif latamDocType.internal_type == 'invoice' and move.move_type == 'in_invoice':
            iTiDE = 4 ## autofactura
        else:
            raise ValidationError("El tipo de documento %s no esta contemplado" % move.name)
        #
        if iTiDE in (5,6): # NC/ND
            for rec in moveRev_ids:
                docAso = {}
                rec_xmlgen = {}
                iTipDocAso = 1 if rec.journal_id.l10n_avatar_py_poe_system == 'FAE' else 2
                docAso.update({ 'iTipDocAso': iTipDocAso}) # H002
                docAso.update({ 'dDesTipDocAso': 'Electrónico' if iTipDocAso == 1 else 'Impreso'}) # H003
                if iTipDocAso == 1: # Electronico
                    if not rec.l10n_avatar_py_edi_cdc:
                        raise ValidationError("El documento asociado %s no tiene el valor del CDC" % rec.name)
                    docAso.update({ 'dCdCDERef': rec.l10n_avatar_py_edi_cdc}) # H004
                    if xmlgen:
                        rec_xmlgen.update({ 'formato': docAso['iTipDocAso']})
                        rec_xmlgen.update({ 'cdc': docAso['dCdCDERef']})
                else:
                    if not rec.l10n_avatar_py_authorization_code:
                        raise ValidationError("El documento asociado %s no tiene los datos de tmbrado" % rec.name)
                    docAso.update({ 'dNTimDI': rec.l10n_avatar_py_authorization_code}) # H005
                    dEstDocAso, dPExpDocAso, dNumDocAso = rec.l10n_latam_document_number.split('-')
                    docAso.update({ 'dEstDocAso': dEstDocAso}) # H006
                    docAso.update({ 'dPExpDocAso': dPExpDocAso}) # H007
                    docAso.update({ 'dNumDocAso': dNumDocAso}) # H008
                    iTipoDocAso = 0
                    if rec.l10n_latam_document_type_id.internal_type == 'invoice':
                        docAso.update({ 'iTipoDocAso': 1}) # H009
                        docAso.update({ 'dDTipoDocAso': 'Factura'}) # H010
                    elif rec.l10n_latam_document_type_id.internal_type == 'credit_note':
                        docAso.update({ 'iTipoDocAso': 2}) # H009
                        docAso.update({ 'dDTipoDocAso': 'Nota de crédito'}) # H010
                    elif rec.l10n_latam_document_type_id.internal_type == 'debit_note':
                        docAso.update({ 'iTipoDocAso': 3}) # H009
                        docAso.update({ 'dDTipoDocAso': 'Nota de débito'}) # H010
                    else:
                        raise ValidationError("El tipo de documento asociaso %s no es válido" % rec.name)
                    docAso.update({ 'dFecEmiDI': rec.invoice_date.strftime("%Y-%m-%d")}) # H011
                    if xmlgen:
                        rec_xmlgen.update({ 'formato': docAso['iTipDocAso']})
                        rec_xmlgen.update({ 'timbrado': docAso['dNTimDI']})
                        rec_xmlgen.update({ 'establecimiento': docAso['dEstDocAso']})
                        rec_xmlgen.update({ 'punto': docAso['dPExpDocAso']})
                        rec_xmlgen.update({ 'numero': docAso['dNumDocAso']})
                        rec_xmlgen.update({ 'tipoDocumentoImpreso': docAso['iTipoDocAso']})
                        rec_xmlgen.update({ 'tipo': docAso['iTipoDocAso']})
                        rec_xmlgen.update({ 'fecha': docAso['dFecEmiDI']})
                        rec_xmlgen.update({ 'dd': docAso['']})
                if xmlgen:
                    gCamDEAsoc.append(rec_xmlgen)
                else:
                    gCamDEAsoc.append(docAso)
        else:
            # Autofactura
            docAso = {}
            docAso.update({ 'iTipCons': 1}) # H014
            docAso.update({ 'dDesTipCons': 'Constancia de no ser contribuyente'}) # H015
            docAso.update({ 'dNumCons': move.partner_id.l10n_avatar_py_taxpayer_number})
            docAso.update({ 'dNumControl': move.partner_id.l10n_avatar_py_taxpayer_control})
            rec_xmlgen = {}
            rec_xmlgen.update({ 'constanciaTipo': docAso['iTipCons']})
            rec_xmlgen.update({ 'constanciaNumero': docAso['dNumCons']})
            rec_xmlgen.update({ 'constanciaControl': docAso['dNumControl']})
            if xmlgen:
                gCamDEAsoc.append(rec_xmlgen)
            else:
                gCamDEAsoc.append(docAso)
        return gCamDEAsoc

    ###
    def _save_json_files(self, params, data, options):
        path_vscode_logs = "/home/odoo/ODOO/General18/Backend/xmlgen/jsons"
        if path.exists(path_vscode_logs):
            with open(path_vscode_logs + '/params.json', 'w') as f:
                json.dump(params, f, indent=4)
            with open(path_vscode_logs + '/data.json', 'w') as f:
                json.dump(data, f, indent=4)
            with open(path_vscode_logs + '/options.json', 'w') as f:
                json.dump(options, f, indent=4)

    def _get_sifen_xmlgen( self, move:AccountMove):
        params = {}
        data = {}
        options = {}
        if move.currency_id != move.company_currency_id:
            options.update({ 'partialTaxDecimals': 2})
        #
        data.update(self._get_sifen_gOpeDE(move, xmlgen=True))
        data.update(self._get_sifen_gTimb(move, xmlgen=True))
        if data.get('timbradoNumero') != None:
            params.update({ 'timbradoNumero': data.get('timbradoNumero')})
        if data.get('serie') != None:
            params.update({ 'serie': data.get('serie')})
        if data.get('timbradoFecha') != None:
            params.update({ 'timbradoFecha': data.get('timbradoFecha')})
        data.update(self._get_sifen_gOpeCom(move, xmlgen=True))
        params.update(self._get_sifen_gEmis(move.company_id, xmlgen=True, is_edi=True, establecimiento=move.journal_id.l10n_avatar_py_branch))
        params.update({ 'actividadesEconomicas': self._get_sifen_gActEco(move.company_id,xmlgen=True)})
        data.update({ 'cliente': self._get_sifen_gDatRec(move,xmlgen=True)})
        if move.move_type in ('in_invoice','out_invoice'):
            data.update({ 'factura': self._get_sifen_gCamFE(move,xmlgen=True)})
        if move.move_type == 'in_invoice':
            data.update({ 'autoFactura': self._get_sifen_gCamAE(move.partner_id, move.journal_id, xmlgen=True)})
        if move.move_type == 'out_refund':
            data.update({ 'notaCreditoDebito': self._get_sifen_gCamNCDE(move,xmlgen=True)})
        data.update({ 'condicion': self._get_sifen_gCamCond(move,xmlgen=True)})
        data.update({ 'fecha': datetime.now().strftime("%Y-%m-%dT%H:%M:%S")})
        #
        items = []
        for item in move.invoice_line_ids:
            if item.display_type == 'product':
                items.append(self._get_sifen_gCamItem( item, xmlgen=True))
        data.update({ 'items': items})
        if move.move_type == 'out_refund':
            data.update({ 'documentoAsociado': self._get_sifen_gCamDEAsoc(move, xmlgen=True)})
        self._save_json_files( params, data, options)
        all_json = {}
        all_json.update({'empresa':move.company_id.partner_id.vat.split('-')[0]})
        all_json.update({'servicio':'de'})
        all_json.update({'params':params})
        all_json.update({'data':data})
        all_json.update({'options':options})
        return all_json

    def _call_sifen( self, url, data):
        response = requests.post(url, json=json.loads(json.dumps(data)), allow_redirects=False)
        if response.status_code == 301:
            response = requests.post( response.headers['Location'],  json=json.loads(json.dumps(data)))
        if response.status_code != 200:
            _logger.error( "Error: %s" % str(response.status_code) + "-" + response.text)
            raise UserError( "Error en la llamada [%s]" % str(response.status_code) + "-" + response.text)
        res = json.loads(response.text)
        if res.get('code') != None and int(res.get('code')) == 0:
            return res.get('payload')
        else:
            raise UserError( "Error en la llamada [%s]" % response.text)

    def _process_sifen_ResEnviLoteDe( self, move:AccountMove, data):
        url = 'https://3df.com.ar/pyrite' if move.company_id.l10n_avatar_py_is_edi_test else 'http://global.avatar.com.py/pyrite'
        payload = self._call_sifen( url, data)
        lote = move.l10n_avatar_py_edi_lote_ids
        lote.response_json = payload
        if payload.get('ns2:rResEnviLoteDe') == None:
            raise UserError( str(payload))
        if payload['ns2:rResEnviLoteDe'].get('ns2:dFecProc') != None:
            fecha = dt.datetime.strptime(payload['ns2:rResEnviLoteDe'].get('ns2:dFecProc')[:19], "%Y-%m-%dT%H:%M:%S")
            TZ_HS = int(payload['ns2:rResEnviLoteDe'].get('ns2:dFecProc')[19:22])
            Tz_MM = int(payload['ns2:rResEnviLoteDe'].get('ns2:dFecProc')[23:])
            
            lote.request_date = fecha - dt.timedelta(hours=TZ_HS,minutes=Tz_MM)
        lote.resenvilotede_dcodres = payload['ns2:rResEnviLoteDe'].get('ns2:dCodRes')
        lote.resenvilotede_dmsgres = payload['ns2:rResEnviLoteDe'].get('ns2:dMsgRes')
        lote.lote_number = payload['ns2:rResEnviLoteDe'].get('ns2:dProtConsLote')
        lote.resenvilotede_dtpoproces = payload['ns2:rResEnviLoteDe'].get('ns2:dTpoProces')
        lote.resenvilotede_res_id = payload['id']
        lote.resenvilotede_res_qr = payload['qr']
        lote.resenvilotede_res_cdc = payload['cdc']

    def _get_sifen_ResEnviConsLoteDe( self, data, lote:PyEdiLote, is_edi_test=True):
        url = 'https://3df.com.ar/pyrite' if is_edi_test else 'http://global.avatar.com.py/pyrite'
        payload = self._call_sifen( url, data)
        if payload.get('ns2:rResEnviConsLoteDe') == None:
            raise UserError( str(payload))
        if payload['ns2:rResEnviConsLoteDe'].get('ns2:dFecProc') != None:
            fecha = dt.datetime.strptime(payload['ns2:rResEnviConsLoteDe'].get('ns2:dFecProc')[:19], "%Y-%m-%dT%H:%M:%S")
            TZ_HS = int(payload['ns2:rResEnviConsLoteDe'].get('ns2:dFecProc')[19:22])
            Tz_MM = int(payload['ns2:rResEnviConsLoteDe'].get('ns2:dFecProc')[23:])
            lote.response_date = fecha - dt.timedelta(hours=TZ_HS,minutes=Tz_MM)
        lote.resenviconslotede_dcodreslot = payload['ns2:rResEnviConsLoteDe'].get('ns2:dCodResLot')
        lote.resenviconslotede_dmsgreslot = payload['ns2:rResEnviConsLoteDe'].get('ns2:dMsgResLot')
        gResProcLote = payload['ns2:rResEnviConsLoteDe'].get('ns2:gResProcLote')
        gResProc = None
        if gResProcLote != None and str(type(gResProcLote)) == "<class 'list'>":
            for rec in gResProcLote:
                lote.resenviconslotede_id = rec.get('ns2:id')
                lote.resenviconslotede_destrec = rec.get('ns2:dEstRes')
                lote.resenviconslotede_dprotaut = rec.get('ns2:dProtAut')
                gResProc = rec.get('ns2:gResProc')
        elif gResProcLote != None and str(type(gResProcLote)) == "<class 'dict'>":
            lote.resenviconslotede_id = gResProcLote.get('ns2:id')
            lote.resenviconslotede_destrec = gResProcLote.get('ns2:dEstRes')
            lote.resenviconslotede_dprotaut = gResProcLote.get('ns2:dProtAut')
            gResProc = gResProcLote.get('ns2:gResProc')
        if gResProc != None and str(type(gResProcLote)) == "<class 'list'>":
            for rec in gResProc:
                lote.resenviconslotede_dcodres = rec.get('ns2:dCodRes')
                lote.resenviconslotede_dmsgres = rec.get('ns2:dMsgRes')
        elif gResProc != None and str(type(gResProcLote)) == "<class 'dict'>":
            lote.resenviconslotede_dcodres = gResProc.get('ns2:dCodRes')
            lote.resenviconslotede_dmsgres = gResProc.get('ns2:dMsgRes')


        
