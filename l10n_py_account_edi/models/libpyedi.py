#

from odoo import _
from odoo.addons.account.models.account_move import AccountMove
from odoo.addons.account.models.account_move_line import AccountMoveLine
from odoo.addons.base.models.res_partner import Partner
from odoo.addons.base.models.res_company import Company
from odoo.addons.base.models.res_users import Users
from odoo.exceptions import UserError, ValidationError

from datetime import datetime
from random import randint
import pytz
import stdnum.py.ruc
from os import path
import json
import logging

_logger = logging.getLogger(__name__)

def _validate_dCodSeg( moveId:AccountMove, code):
    acc = moveId.env['account.move'].search([('l10n_py_dnit_ws_random_code', '=', code)])
    if len(acc) > 0:
        return True
    else:
        return False

def _save_json_files(params,data,options):
    path_vscode_logs = "/opt/Odoo/odoo-18.0.developer/odoo-custom-addons/.vscode/TestLibXML/data"
    if path.exists(path_vscode_logs):
        with open(path_vscode_logs + '/params.json', 'w') as f:
            json.dump(params, f, indent=4)
        with open(path_vscode_logs + '/data.json', 'w') as f:
            json.dump(data, f, indent=4)
        with open(path_vscode_logs + '/options.json', 'w') as f:
            json.dump(options, f, indent=4)

def _generate_dCodSeg(moveId:AccountMove):
    pin_length = 9
    number_max = (10**pin_length) - 1
    number = randint( 0, number_max)
    delta = (pin_length - len(str(number))) * '0'
    random_code = '%s%s' % (delta,number)
    condition = _validate_dCodSeg( moveId, random_code)
    if condition:
        _generate_dCodSeg(moveId)
    moveId.l10n_py_dnit_ws_random_code = random_code
    return random_code

def _get_document_type( docType:str):
    _MOVE_TYPES = {'entry': '0', 'out_invoice': '1', 'out_refund': '5', 'in_invoice': '4',
                   'in_refund': '0', 'out_receipt': '7', 'in_receipt': '0', }
    return _MOVE_TYPES[docType]

def _get_sysdate(user:Users):
    now = datetime.now()
    tz = pytz.timezone(user.tz) or pytz.utc
    return pytz.utc.localize(now).astimezone(tz)

# No se esta usando
def _get_dateTZ(date:datetime, user:Users):
    now = date
    tz = pytz.timezone(user.tz) or pytz.utc
    new_date = pytz.utc.localize(now).astimezone(tz)
    return new_date

def _get_tipo_impuesto_gral(lines:AccountMoveLine):
    globalTaxTye = '0'
    for rec in lines:
        if rec.display_type == "product":
            taxType = rec.tax_ids.l10n_py_tax_type
            if globalTaxTye == "0":
                globalTaxTye = taxType
            elif globalTaxTye == "5" and taxType == "2":
                globalTaxTye = "2"
            elif globalTaxTye == "5" and taxType == "4":
                globalTaxTye = "4"
            elif globalTaxTye == "3" and (taxType == "1" or taxType == "5"):
                globalTaxTye = "5"
            elif globalTaxTye == "3" and taxType == "2":
                globalTaxTye = "2"
            elif globalTaxTye == "1" and (taxType == "3" or taxType == "5"):
                globalTaxTye = "5"
            elif globalTaxTye == "1" and taxType == "2":
                globalTaxTye = "2"
    return int(globalTaxTye)

def _get_format_ruc(vat):
    if vat.split("-").__len__ == 2:
        return vat
    if stdnum.py.ruc.is_valid(vat):
        return stdnum.py.ruc.format(vat)
    return stdnum.py.ruc.format(vat + stdnum.py.ruc.calc_check_digit(vat)) 

#############################

# B Campos inherentes a la operacion de Documentos Electronicos (B001-B099)
def _get_gOpeDE(moveId:AccountMove):
    gOpeDE = {}
    gOpeDE.update({"iTipEmi":1}) #B002
    gOpeDE.update({"dCodSeg":_generate_dCodSeg(moveId)}) #B004
    #gOpeDE.update({"dInfoEmi":123}) #B005   No implementado
    #gOpeDE.update({"dInfoFisc":123}) #B006   No implementado
    return gOpeDE

# C Campos de datos del Timbrado (C001-C099)
def _get_gTimb(moveId:AccountMove):
    gTimb = {}
    iTiDE = int(_get_document_type(moveId.move_type))
    gTimb.update({"iTiDE":iTiDE}) #C002
    dnumTim = moveId.journal_id.l10n_py_dnit_timbrado
    dFecIniT = moveId.journal_id.l10n_py_dnit_timbrado_start_date
    if moveId.company_id.l10n_py_dnit_ws_environment == 'testing':
        dnumTim = moveId.journal_id.l10n_py_dnit_timbrado_test
        dFecIniT = moveId.journal_id.l10n_py_dnit_timbrado_start_date_test
    if not dnumTim:
        raise ValidationError("No se especifico el numero de timbrado en el diario")
    if not dFecIniT:
        raise ValidationError("No se especifico la fecha del timbrado en el diario")
    if dnumTim.split('-').__len__() == 2:
        gTimb.update({"dnumTim":dnumTim.split('-')[0]}) #C004
        gTimb.update({"dSerieNum":dnumTim.split('-')[1]}) #C010
    else:
        gTimb.update({"dnumTim":dnumTim}) #C004
    establecimiento, pos, numero = moveId.l10n_latam_document_number.split('-')
    gTimb.update({"dEst":establecimiento}) #C005
    gTimb.update({"dPunExp":pos}) #C006
    gTimb.update({"dNumDoc":numero}) #C007
    gTimb.update({"dFecIniT":dFecIniT.strftime("%Y-%m-%d")}) #C008
    return gTimb

# D Campos Generales del Docuemto Electronico (D001-D299)
def _get_gDatGralOpe(moveId:AccountMove):
    gDatGralOpe = {}
    #gDatGralOpe.update({"dFeEmiDE":_get_sysdate(moveId.env['res.users'].browse([2])).strftime("%Y-%m-%dT%H:%M:%S")}) #D002
    gDatGralOpe.update({"dFeEmiDE":moveId.invoice_date.strftime("%Y-%m-%dT%H:%M:%S")}) #D002
    return gDatGralOpe

# D1 Campos inherentes a la operacion comercial (D010-D099)
def _get_gOpeCom(moveId:AccountMove):
    gOpeCom = {}
    if moveId.move_type == 'out_invoice' or moveId.move_type == 'in_invoice':
        gOpeCom.update({"iTipTra":moveId.l10n_py_dnit_concept}) #D011
    gOpeCom.update({"iTImp":_get_tipo_impuesto_gral(moveId.invoice_line_ids)}) #D013
    if moveId.move_type == "in_invoice":
        gOpeCom.update({"iTImp":4}) #D013
    gOpeCom.update({"cMoneOpe":moveId.currency_id.name}) #D015
    if moveId.currency_id.name != 'PYG':
        gOpeCom.update({"dCondTiCam":1}) #D017
        gOpeCom.update({"dTiCam":1 / moveId.invoice_currency_rate}) #D018
    return gOpeCom

# D2 Campos que identifican al emisor del Documento Electronico (D100-D129)
def _get_gEmis(companyId:Company):
    gEmis = {}
    ruc = _get_format_ruc(companyId.vat)
    gEmis.update({"dRucEm":ruc.split('-')[0]}) #D101
    gEmis.update({"dDVEmi":ruc.split('-')[1]}) #D102
    gEmis.update({"iTipCont":2 if companyId.partner_id.is_company else 1}) #D103
    cTipReg = companyId.l10n_py_regime_type_id.code
    if cTipReg and cTipReg > 0:
        gEmis.update({"cTipReg":cTipReg}) #D104
    gEmis.update({"dNomEmi":companyId.name}) #D105
    if companyId.l10n_py_dnit_ws_environment == 'testing':
        gEmis.update({"dNomEmi":"DE generado en ambiente de prueba - sin valor comercial ni fiscal"}) #D105
        gEmis.update({"dNomFanEmi":companyId.name}) #D106
    gEmis.update({"dDirEmi":companyId.street}) #D107
    gEmis.update({"dNumCas":companyId.l10n_py_house if companyId.l10n_py_house else '1'}) #D108
    if companyId.street2:
        gEmis.update({"dCompDir1":companyId.street2}) #D109
    gEmis.update({"cDepEmi":companyId.state_id.code}) #D111
    if companyId.l10n_py_district_id.code:
        gEmis.update({"cDisEmi":companyId.l10n_py_district_id.code}) #D113
    gEmis.update({"cCiuEmi":companyId.l10n_py_city_id.code}) #D115
    if companyId.phone:
        gEmis.update({"dTelEmi":companyId.phone}) #D117
    else:
        raise ValidationError("Es obligatorio definir el telefono en la compania")
    if companyId.email:
        gEmis.update({"dEmailE":companyId.email}) #D118
    else:
        raise ValidationError("Es obligatorio definir el mail en la compania")
    return gEmis

# D2.1 Campos que describen la actividad economica del emisor (D130-D139)
def _get_gActEco(companyId:Company):
    gActEco = []
    for rec in companyId.l10n_py_economic_activity_ids:
        vector = {}
        vector.update({"cActEco":rec.code})
        vector.update({"cDesActEco":rec.name})
        gActEco.append(vector)
    return gActEco

def _get_xmlgen_actividadesEconomicas(companyId:Company):
    actD2 = _get_gActEco(companyId)
    actividades = []
    for rec in actD2:
        actividad = {}
        actividad.update({"codigo":rec.get("cActEco")})
        actividad.update({"descripcion":rec.get("cDesActEco")})
        actividades.append(actividad)
    return actividades

# D2.2 Campos que identifican al responsable de la generacion del DE (D140-D160)
def _get_gRespDE():
    gRespDE = {}
    return gRespDE

# D3 Campos que identifican al receptor del Documento Electronico DE (D200-D299)
def _get_gDatRec(moveId:AccountMove):
    gDatRec = {}
    if moveId.move_type != 'in_invoice':
        # Datos del Partner
        if moveId.partner_id.l10n_latam_identification_type_id.l10n_py_dnit_code == '0' and moveId.partner_id.country_id.l10n_py_alpha_code == "PRY":
            gDatRec.update({"iNatRec":1}) #D201
            gDatRec.update({"iTiContRec":2 if moveId.partner_id.is_company else 1}) #D205
            ruc = _get_format_ruc(moveId.partner_id.vat)
            gDatRec.update({"dRucRec":ruc.split("-")[0]}) #D206
            gDatRec.update({"dDVRec":ruc.split("-")[1]}) #D207
        else:
            gDatRec.update({"iNatRec":2}) #D201
            gDatRec.update({"iTipIDRec":moveId.partner_id.l10n_latam_identification_type_id.l10n_py_dnit_code}) #D208
            if moveId.partner_id.country_id.l10n_py_alpha_code == "PRY":
                gDatRec.update({"dNumIDRec":moveId.partner_id.vat}) #D210

        gDatRec.update({"iTiOpe":1 if moveId.partner_id.is_company else 2}) #D202
        if moveId.partner_id.l10n_latam_identification_type_id.l10n_py_dnit_code and moveId.partner_id.l10n_latam_identification_type_id.l10n_py_dnit_code != '0':
            if moveId.partner_id.country_id.l10n_py_alpha_code == 'PRY':
                gDatRec.update({"iTiOpe":2}) #D202
            else:
                gDatRec.update({"iTiOpe":4}) #D202
        else:
            gDatRec.update({"iTiOpe":2}) #D202
        if moveId.partner_id.country_id.l10n_py_alpha_code != "PRY":
            gDatRec.update({"iTiOpe":4}) #D202
        gDatRec.update({"cPaisRec":moveId.partner_id.country_id.l10n_py_alpha_code}) #D203
        #
        gDatRec.update({"dNomRec":moveId.partner_id.name}) #D211
        if moveId.partner_id.street and moveId.partner_id.country_id.l10n_py_alpha_code == "PRY":
            gDatRec.update({"dDirRec":moveId.partner_id.street}) #D213
            gDatRec.update({"dNumCasRec":moveId.partner_id.l10n_py_house if moveId.partner_id.l10n_py_house else 1}) #D218
            if moveId.partner_id.state_id.code:
                gDatRec.update({"cDepRec":moveId.partner_id.state_id.code}) #D219
            else:
                raise ValidationError("Es obligatorio definir el departamento del cliente")
            if moveId.partner_id.l10n_py_district_id.code:
                gDatRec.update({"cDisRec":moveId.partner_id.l10n_py_district_id.code}) #D221
            if moveId.partner_id.l10n_py_city_id.code:
                gDatRec.update({"cCiuRec":moveId.partner_id.l10n_py_city_id.code}) #D223
            else:
                raise ValidationError("Es obligatorio definir la ciudad del cliente")
    else:
        # Datos de la compania
        gDatRec.update({"iNatRec":1}) #D201
        gDatRec.update({"iTiOpe":2}) #D202
        gDatRec.update({"cPaisRec":"PRY"}) #D203
        gDatRec.update({"iTiContRec":2}) #D205
        ruc = _get_format_ruc(moveId.company_id.vat)
        gDatRec.update({"dRucRec":ruc.split("-")[0]}) #D206
        gDatRec.update({"dDVRec":ruc.split("-")[1]}) #D207
        gDatRec.update({"qwerty":12345})
        gDatRec.update({"dNomRec":moveId.company_id.name}) #D211
        gDatRec.update({"dDirRec":moveId.company_id.street}) #D213
        gDatRec.update({"dNumCasRec":moveId.company_id.l10n_py_house if moveId.company_id.l10n_py_house else 1}) #D218
        gDatRec.update({"cCiuRec":moveId.company_id.l10n_py_city_id.code}) #D223

    return gDatRec

def _get_xmlgen_cliente(moveId:AccountMove):
    gDatRec = _get_gDatRec(moveId)
    cliente = {}

    cliente.update({"contribuyente":True if int(gDatRec.get("iNatRec") or 0) == 1 else False})
    if gDatRec.get("dRucRec") and gDatRec.get("dRucRec") != None:
        cliente.update({"ruc":gDatRec["dRucRec"] + "-" + gDatRec["dDVRec"]})
    cliente.update({"razonSocial":gDatRec.get("dNomRec")})
    cliente.update({"tipoOperacion":gDatRec.get("iTiOpe")})
    if gDatRec.get("dDirRec") and gDatRec.get("dDirRec") != None:
        cliente.update({"direccion":gDatRec.get("dDirRec")})
        cliente.update({"numeroCasa":gDatRec.get("dNumCasRec")})
    if gDatRec.get("cDepRec") and gDatRec.get("cDepRec") != None:
        cliente.update({"departamento":int(gDatRec.get("cDepRec") or 0)})
    if gDatRec.get("cDisRec") and gDatRec.get("cDisRec") != None:
        cliente.update({"distrito":gDatRec.get("cDisRec")})
    if gDatRec.get("cCiuRec") and gDatRec.get("cCiuRec") != None:
        cliente.update({"ciudad":gDatRec.get("cCiuRec")})
    cliente.update({"pais":gDatRec.get("cPaisRec")})
    cliente.update({"tipoContribuyente":gDatRec.get("iTiContRec")})
    if gDatRec.get("iTipIDRec") and gDatRec.get("iTipIDRec") != None:
        cliente.update({"documentoTipo":gDatRec.get("iTipIDRec")})
    if gDatRec.get("dNumIDRec") and gDatRec.get("dNumIDRec") != None:
        cliente.update({"documentoNumero":gDatRec.get("dNumIDRec")})
    #cliente.update({"telefono":12345})
    #cliente.update({"email":12345})
    #cliente.update({"codigo":12345})
    return cliente

# E1 Campos que componen la Factura Electronica (E001-E009)
def _get_gCamFE(moveId:AccountMove):
    gCamFE = {}
    gCamFE.update({"iIndPres":1}) #E011
    # E1.1 Campos de informaciones de compras Publicas (E020-E029)
    gCompPub = {}
    gCamFE.update({"gCompPub":gCompPub}) #E020  Pendiente de implementacion
    return gCamFE

def _get_xmlgen_factura(moveId:AccountMove):
    gCamFE = _get_gCamFE(moveId)
    factura = {}
    factura.update({"presencia":gCamFE.get("iIndPres")})
    return factura

# E4. Campos que componen la Autofactura Electronica AFE (E300-E399)
def _get_gCamAE( partnerId:Partner, companyId:Company):
    gCamAE = {}
    gCamAE.update({"iNatVen": 1 if partnerId.country_code == 'PY' else 2}) # E301
    iTipIDVen = partnerId.l10n_latam_identification_type_id.l10n_py_dnit_code
    if iTipIDVen in ('1','2','3','4'):
        gCamAE.update({"iTipIDVen": int(iTipIDVen)}) # E304
    else:
        msg = "Tipo de documento inválido del partner (%s)" % partnerId.l10n_latam_identification_type_id.name
        msg = msg + "\n  Valores posibles:\n   Cédula Paraguaya, Pasaporte, Cédula extrangera, Carnet de Residencia"
        raise ValidationError(msg)
    dNumIDVen = partnerId.vat
    if not dNumIDVen or dNumIDVen == None:
        raise ValidationError("Némero de documento sin definir para el Vendedor")
    gCamAE.update({"dNumIDVen": dNumIDVen}) #E306
    gCamAE.update({"dNomVen": partnerId.name}) #E307
    if gCamAE.get("iNatVen") == 2:
        gCamAE.update({"dDirVen": companyId.street}) #E308
        gCamAE.update({"dNumCasVen": companyId.l10n_py_house if companyId.l10n_py_house else 1}) #E309
        gCamAE.update({"cDepVen": companyId.state_id.code}) #E310
        gCamAE.update({"dDesDepVen": companyId.state_id.name}) #E311
        cDisVen = companyId.l10n_py_district_id.code
        if cDisVen and cDisVen != None:
            gCamAE.update({"cDisVen": cDisVen}) #E312
            gCamAE.update({"dDesDisVen": companyId.l10n_py_district_id.name}) #E312
        cCiuVen = companyId.l10n_py_city_id.code
        if not cCiuVen or cCiuVen == None:
            raise ValidationError("Falta definir la ciudad en la compañia")
        else:
            gCamAE.update({"cCiuVen": cCiuVen}) #E314
            gCamAE.update({"dDesCiuVen": companyId.l10n_py_city_id.name}) #E315
    else:
        gCamAE.update({"dDirVen": partnerId.street}) #E308
        if not partnerId.street or partnerId.street == None:
            raise ValidationError("Falta definir la calle del Vendedor")
        gCamAE.update({"dNumCasVen": partnerId.l10n_py_house if partnerId.l10n_py_house else 1}) #E309
        gCamAE.update({"cDepVen": partnerId.state_id.code}) #E310
        if not partnerId.state_id:
            raise ValidationError("Falta definir el departamento del Proveedor")
        cDisVen = partnerId.l10n_py_district_id.code
        if cDisVen and cDisVen != None:
            gCamAE.update({"cDisVen": cDisVen}) #E312
        cCiuVen = partnerId.l10n_py_city_id.code
        if not cCiuVen or cCiuVen == None:
            raise ValidationError("Falta definir la ciudad en el Proveedor")
        else:
            gCamAE.update({"cCiuVen": cCiuVen}) #E314
    gCamAE.update({"dDirProv": companyId.street}) #E316
    gCamAE.update({"cDepProv": companyId.state_id.code}) #E317
    gCamAE.update({"dDesDepProv": companyId.state_id.name}) #E318
    cDisProv = companyId.l10n_py_district_id.code
    if cDisProv and cDisProv != None:
            gCamAE.update({"cDisProv": cDisProv}) #E319
            gCamAE.update({"dDesDisProv": companyId.l10n_py_district_id.name}) #E320
    gCamAE.update({"cCiuProv": companyId.l10n_py_city_id.code}) #E321
    gCamAE.update({"dDesCiuProv": companyId.l10n_py_city_id.name}) #E321
    return gCamAE

def _get_xmlgen_autofactura( partnerId:Partner, companyId:Company):
    gCamAE = _get_gCamAE( partnerId, companyId)
    autofactura = {}
    autofactura.update({"tipoVendedor":gCamAE.get("iNatVen")})
    autofactura.update({"documentoTipo":gCamAE.get("iTipIDVen")})
    autofactura.update({"documentoNumero":gCamAE.get("dNumIDVen")})
    autofactura.update({"nombre":gCamAE.get("dNomVen")})
    autofactura.update({"direccion":gCamAE.get("dDirVen")})
    autofactura.update({"numeroCasa":gCamAE.get("dNumCasVen")})
    autofactura.update({"departamento":int(gCamAE.get("cDepVen") or 0)})
    autofactura.update({"departamdepartamentoDescripcionento":(gCamAE.get("dDesDepVen"))})
    if gCamAE.get("cDisVen") != None:
        autofactura.update({"distrito":gCamAE.get("cDisVen")})
        autofactura.update({"distritoDescripcion":gCamAE.get("dDesDisVen")})
    autofactura.update({"ciudad":gCamAE.get("cCiuVen")})
    autofactura.update({"ciudadDescripcion":gCamAE.get("dDesCiuVen")})
    ubicacion = {}
    ubicacion.update({"lugar":gCamAE.get("dDirProv")})
    ubicacion.update({"departamento":int(gCamAE.get("cDepProv") or 0)})
    ubicacion.update({"departamentoDescripcion":(gCamAE.get("dDesDepProv"))})
    if gCamAE.get("cDisProv") != None:
        ubicacion.update({"distrito":gCamAE.get("cDisProv")})
        ubicacion.update({"distritoDescripcion":gCamAE.get("dDesDisProv")})
    ubicacion.update({"ciudad":gCamAE.get("cCiuProv")})
    ubicacion.update({"ciudadDescripcion":gCamAE.get("dDesCiuProv")})
    autofactura.update({"ubicacion":ubicacion})
    transaccion = {}
    transaccion.update({"lugar":gCamAE.get("dDirProv")})
    transaccion.update({"departamento":int(gCamAE.get("cDepProv") or 0)})
    transaccion.update({"departamentoDescripcion":(gCamAE.get("dDesDepProv"))})
    if gCamAE.get("cDisProv") != None:
        transaccion.update({"distrito":gCamAE.get("cDisProv")})
        transaccion.update({"distritoDescripcion":gCamAE.get("dDesDisProv")})
    transaccion.update({"ciudad":gCamAE.get("cCiuProv")})
    transaccion.update({"ciudadDescripcion":gCamAE.get("dDesCiuProv")})
    autofactura.update({"transaccion":transaccion})
    return autofactura

# E5 Campos que componen la Nota de Credito/Debito Electronica (E400-E499)
def _get_gCamNCDE():
    gCamNCDE = {}
    gCamNCDE.update({"iMotEmi":1})
    return gCamNCDE

def _get_xmlgen_notaCreditoDebito():
    gCamNCDE = _get_gCamNCDE()
    notaCreditoDebito = {}
    notaCreditoDebito.update({"motivo":gCamNCDE.get("iMotEmi")})
    return notaCreditoDebito

# E6 Campos que componene la Nota de Remision Electronica (E500-E599)
def _get_gCamNRE():
    gCamNRE = {}
    gCamNRE.update({"iMotEmiNR":12345}) #E501
    gCamNRE.update({"iRespEmiNR":12345}) #E503
    return gCamNRE

def _get_xmlgen_remision():
    gCamNRE = _get_gCamNRE()
    remision = {}
    #remision.update({"motivo":gCamNRE.get("iMotEmiNR")})
    #remision.update({"tipoResponsable":gCamNRE.get("iRespEmiNR")})
    return remision

# E7 Campos que describen la condicion de la operacion (E600-E699)
def _get_gCamCond(moveId:AccountMove):
    gCamCond = {}
    iCondOpe = 1
    difDays = (moveId.invoice_date_due - (moveId.invoice_date or datetime.now())).days
    # Por ahora lo dejamos fijo en pago al contado
    #if difDays > 15:
    #    iCondOpe = 2
    gCamCond.update({"iCondOpe":iCondOpe}) #E601
    if iCondOpe == 1:
        gCamCond.update({"gPaConEIni":_get_gPaConEIni(moveId)}) #E605
    return gCamCond

# E7.1 Campos que describen la forma de pago de la operacion al contado o del monto de la entrega inicial (E605-E619)
def _get_gPaConEIni(moveId:AccountMove):
    gPaConEIni = {}
    iTiPago = 1 # Fijo en efectivo
    gPaConEIni.update({"iTiPago":iTiPago}) #E606
    gPaConEIni.update({"dMonTiPag":moveId.amount_total}) #E608
    gPaConEIni.update({"cMoneTiPag":moveId.currency_id.name}) #E609
    if moveId.currency_id.name != 'PYG':
        gPaConEIni.update({"dTiCamTiPag":1 / moveId.invoice_currency_rate}) #E611
    return gPaConEIni

# E7.1.1 Campos que describen el pago o entrega inicial de la operacion con tarjeta de credito/debito
# E7.1.2 Campos que describen el pago o entrega inicial de la operacion con cheque (E630-E639)

# E7.2 Campos que describen la operacion a credito (E640-E649)
# E7.2.1 Campos que describen la las cuotas (E650-E659)

def _get_xmlgen_condicion(moveId:AccountMove):
    gCamCond = _get_gCamCond(moveId)
    gPaConEIni = gCamCond.get("gPaConEIni") or {}
    condicion = {}
    entrega = {}
    entrega.update({"tipo":gPaConEIni.get("iTiPago")})
    entrega.update({"monto":gPaConEIni.get("dMonTiPag")})
    entrega.update({"moneda":gPaConEIni.get("cMoneTiPag")})
    entrega.update({"cambio":gPaConEIni.get("dTiCamTiPag") if gPaConEIni.get("dTiCamTiPag") != None else 0})
    entregas = []
    entregas.append(entrega)
    condicion.update({"tipo":gCamCond.get("iCondOpe")})
    condicion.update({"entregas":entregas})
    return condicion
    
# E8 Campos que describen los items de la operacion (E700-E899)
def _get_gCamItem( lineId:AccountMoveLine):
    gCamItem = {}
    productId = lineId.product_id
    gCamItem.update({"dCodInt":productId.default_code if productId.default_code else productId.id}) #E701
    #gCamItem.update({"dParAranc":12345}) #E702  Por el momento no esta contemplado
    if productId.l10n_py_ncm_code:
        gCamItem.update({"dNCM":productId.l10n_py_ncm_code}) #E703
    #gCamItem.update({"dDncpG":12345}) #E704
    #gCamItem.update({"dDncpE":12345}) #E705
    #gCamItem.update({"dGtin":12345}) #E706
    #gCamItem.update({"dGtinPq":12345}) #E707
    
    #  gCamItem.update({"dDesProSer":productId.name}) #E708
    gCamItem.update({"dDesProSer":lineId.name}) #E708
    gCamItem.update({"cUniMed":productId.uom_id.l10n_py_dnit_code}) #E709
    gCamItem.update({"dCantProSer":lineId.quantity}) #E711
    # E8.1 campos que describen el precio, tipo de cambio y valor total dela operacion pro item (E720-E729)
    gValorItem = {}
    gValorItem.update({"dPUniProSer":lineId.price_unit}) #E721
    if lineId.currency_id.name != 'PYG':
        gValorItem.update({"dTipCamit":1 / lineId.currency_rate}) #E725
    gValorItem.update({"dTotBruOpeItem":lineId.quantity * lineId.price_unit}) #E727
    # E8.1.1 Campos que describen los descuentos, anticipos y valor total por item (EA001-EA050)
    gValorRestaItem = {}
    if lineId.discount > 0:
        gValorRestaItem.update({"dDescItem":lineId.discount * lineId.price_unit / 100}) #Ea002
        gValorRestaItem.update({"dPorcDesIt":lineId.discount}) #EA003
    gValorRestaItem.update({"dTotOpeItem":0}) #EA008   Por ahora no lo necesitamos
    gValorRestaItem.update({"dTotOpeGs":0}) #EA009  Por ahora no lo necesitamos
    gValorItem.update({"gValorRestaItem":gValorRestaItem}) #EA001
    gCamItem.update({"gValorItem":gValorItem}) #E720
    # E8.2 Campos que describen el IVA de la operacion por item (E730-E739)
    nCantIVA = 0
    for rec in lineId.tax_ids:
        gCamIVA = {}
        ivaTipo = 1
        ivaBase = rec.l10n_py_tax_base
        ivaAmount = rec.amount
        if rec.l10n_py_tax_type != 'P' and  rec.l10n_py_tax_type != 'R':
            nCantIVA += 1
            if ivaAmount == 0:
                ivaTipo = 3
                ivaBase = 0
            elif ivaBase < 100 and ivaBase > 0:
                ivaAmount = lineId.tax_ids.amount * 100 / ivaBase
                ivaTipo = 4
            gCamIVA.update({"iAfecIVA":ivaTipo}) #E731
            gCamIVA.update({"dPropIVA":ivaBase}) #E733
            gCamIVA.update({"dTasaIVA":ivaAmount}) #E734
            gCamIVA.update({"dBasGravIVA":0}) #E735  Por ahora no lo necesitamos
            gCamIVA.update({"dLiqIVAItem":0}) #E736  Por ahora no lo necesitamos
            gCamItem.update({"gCamIVA":gCamIVA}) #E730
    if nCantIVA > 1:
        raise ValidationError("No se puede tener mas de un IVA por linea")
    if nCantIVA == 0:
        raise ValidationError("Es obligatorio que cada linea tenga una IVA")
    # E8.4 Grupo de rastreo de la mercaderia (E750-E760)
    gRasMerc = {}
    gCamItem.update({"gRasMerc":gRasMerc}) #E750
    # E8.5 Sector de automotores nuevos y usados (E770-E789)
    gVehNuevo = {}
    gCamItem.update({"gVehNuevo":gVehNuevo}) #E770
    return gCamItem

    """
    gCamItem
{ "dCodInt": "A", "dNCM": "O", "dDesProSer": "A", "cUniMed": "A", "dCantProSer": "N",
  "gValorItem": { "dPUniProSer": "N", "dTipCamit": "O", "dTotBruOpeItem": "N",
    "gValorRestaItem": { "dDescItem": "O", "dPorcDesIt": "O", "dTotOpeItem": "N", "dTotOpeGs": "N", }
    },
  "gCamIVA": { "iAfecIVA": "N", "dPropIVA": "N", "dTasaIVA": "N", },
  "gRasMerc": {},
  "gVehNuevo": {},
}
    """

def _get_xmlgem_item(lineId:AccountMoveLine):
    gCamItem = _get_gCamItem( lineId)
    gValorItem = gCamItem.get("gValorItem") or {}
    gValorRestaItem = gValorItem.get("gValorRestaItem") or {}
    gCamIVA = gCamItem.get("gCamIVA") or {}
    item = {}
    item.update({"codigo":gCamItem.get("dCodInt")})
    item.update({"descripcion":gCamItem.get("dDesProSer")})
    if gCamItem.get("dNCM") != None:
        item.update({"ncm":gCamItem.get("dNCM")})
    item.update({"unidadMedida":gCamItem.get("cUniMed")})
    item.update({"cantidad":gCamItem.get("dCantProSer")})
    item.update({"precioUnitario":gValorItem.get("dPUniProSer")})
    if gValorItem.get("dTipCamit") != None:
        item.update({"cambio":gValorItem.get("dTipCamit")})
    if gValorRestaItem.get("dPorcDesIt") != None:
        item.update({"descuento":gValorRestaItem.get("dDescItem")})
    item.update({"ivaTipo":gCamIVA.get("iAfecIVA")})
    item.update({"ivaBase":gCamIVA.get("dPropIVA")})
    item.update({"iva":gCamIVA.get("dTasaIVA")})
    return item

def _get_xmlgen_items( moveId:AccountMove):
    items = []
    for lineId in moveId.invoice_line_ids:
        if lineId.display_type == 'product':
            items.append(_get_xmlgem_item(lineId))
    return items

# H campos que identifican al documento asociado (H001-H049)
def _get_gCamDEAsoc( moveId:AccountMove):
    gCamDEAsoc = {}
    TYPE_DOC = {
            'entry': '0',
            'out_invoice': '1',
            'out_refund': '2',
            'in_invoice': '0',
            'in_refund': '3',
            'out_receipt': '4',
            'in_receipt': '0',
    }
    iTipDocAso = 1
    reverseMoveId = moveId.reversed_entry_id
    if moveId.move_type == 'in_invoice':
        iTipDocAso = 3 # Para la autofactura
    elif not reverseMoveId.l10n_py_dnit_ws_response_cdc or reverseMoveId.l10n_py_dnit_ws_response_cdc == None:
        iTipDocAso = 2
    gCamDEAsoc.update({"iTipDocAso":iTipDocAso}) #H002
    if iTipDocAso == 1:
        gCamDEAsoc.update({"dCdCDERef":reverseMoveId.l10n_py_dnit_ws_response_cdc}) #H004
    elif iTipDocAso == 2:
        gCamDEAsoc.update({"dNTimDI":reverseMoveId.journal_id.l10n_py_dnit_timbrado}) #H005
        establecimiento, pos, numero = reverseMoveId.l10n_latam_document_number.split('-')
        gCamDEAsoc.update({"dEstDocAso":establecimiento}) #H006
        gCamDEAsoc.update({"dPExpDocAso":pos}) #H007
        gCamDEAsoc.update({"dNumDocAso":numero}) #H008
        gCamDEAsoc.update({"iTipoDocAso":TYPE_DOC[reverseMoveId.move_type]}) #H009
        gCamDEAsoc.update({"dFecEmiDI":reverseMoveId.invoice_date.strftime("%Y-%m-%d")}) #H011
    else:
        gCamDEAsoc.update({"iTipCons":1}) #H014
        gCamDEAsoc.update({"dNumCons":moveId.partner_id.l10n_py_dnit_self_number}) #H016
        gCamDEAsoc.update({"dNumControl":moveId.partner_id.l10n_py_dnit_self_control}) #H017
        if not moveId.partner_id.l10n_py_dnit_self_end_date or moveId.partner_id.l10n_py_dnit_self_end_date < moveId.invoice_date:
            raise ValidationError("El comprobante de no contribuyente para la autofactura se encuentra vencido")
        if not moveId.partner_id.l10n_py_dnit_self_control or not moveId.partner_id.l10n_py_dnit_self_number:
            raise ValidationError("Faltan datos del combrobante de no contribuyente para la autofactura")        
    return gCamDEAsoc

def _get_xmlgen_documentoAsociado(moveId:AccountMove):
    gCamDEAsoc = _get_gCamDEAsoc(moveId)
    documentoAsociado = {}
    documentoAsociado.update({"formato":gCamDEAsoc.get("iTipDocAso")})

    if gCamDEAsoc.get("dCdCDERef") != None:
        documentoAsociado.update({"cdc":gCamDEAsoc.get("dCdCDERef")})
    if gCamDEAsoc.get("iTipoDocAso") != None:
        documentoAsociado.update({"tipo":gCamDEAsoc.get("iTipoDocAso")})
        documentoAsociado.update({"timbrado":gCamDEAsoc.get("dNTimDI")})
        documentoAsociado.update({"establecimiento":gCamDEAsoc.get("dEstDocAso")})
        documentoAsociado.update({"punto":gCamDEAsoc.get("dPExpDocAso")})
        documentoAsociado.update({"numero":gCamDEAsoc.get("dNumDocAso")})
        documentoAsociado.update({"fecha":gCamDEAsoc.get("dFecEmiDI")})
    if gCamDEAsoc.get("iTipCons") != None:
        documentoAsociado.update({"constanciaTipo":gCamDEAsoc.get("iTipCons")})
        documentoAsociado.update({"constanciaNumero":gCamDEAsoc.get("dNumCons")})
        documentoAsociado.update({"constanciaControl":gCamDEAsoc.get("dNumControl")})
    return documentoAsociado
    
###########################################

def get_xmlgen_DE(moveId:AccountMove):
    params = {}
    data = {}
    #
    gEmis = _get_gEmis(moveId.company_id)
    params.update({"version":150})
    params.update({"ruc":gEmis["dRucEm"] + "-" + gEmis["dDVEmi"]})
    params.update({"razonSocial":gEmis.get("dNomEmi")})
    if gEmis.get("dNomFanEmi") and gEmis.get("dNomFanEmi") != None:
        params.update({"nombreFantasia":gEmis.get("dNomFanEmi")})
    params.update({"actividadesEconomicas":_get_xmlgen_actividadesEconomicas(moveId.company_id)})

    gTimb = _get_gTimb(moveId) or {}
    params.update({"timbradoNumero":gTimb.get("dnumTim")})
    if gTimb.get("dSerieNum") and gTimb.get("dSerieNum") != None:
        params.update({"numeroSerie":gTimb.get("dSerieNum")})
    params.update({"timbradoFecha":gTimb.get("dFecIniT")})

    params.update({"tipoContribuyente":gEmis.get("iTipCont")})
    if gEmis.get("cTipReg") and gEmis.get("cTipReg") != None:
        params.update({"tipoRegimen":gEmis.get("cTipReg")})
      
    establecimiento = {}
    establecimiento.update({"codigo":gTimb.get("dEst")})
    establecimiento.update({"direccion":gEmis.get("dDirEmi")})
    establecimiento.update({"numeroCasa":gEmis.get("dNumCas")})
    if gEmis.get("dCompDir1") and gEmis.get("dCompDir1") != None:
        establecimiento.update({"complementoDireccion1":gEmis.get("dCompDir1")})
    establecimiento.update({"departamento":int(gEmis.get("cDepEmi") or 0)})
    if gEmis.get("cDisEmi") and gEmis.get("cDisEmi") != None:
        establecimiento.update({"distrito":gEmis.get("cDisEmi")})
    establecimiento.update({"ciudad":gEmis.get("cCiuEmi")})
    establecimiento.update({"telefono":gEmis.get("dTelEmi")})
    establecimiento.update({"email":gEmis.get("dEmailE")})
    establecimientos = []
    establecimientos.append(establecimiento)
    params.update({"establecimientos":establecimientos})
    #
    iTiDE = gTimb.get("iTiDE") #C002
    data.update({"tipoDocumento":iTiDE})
    data.update({"establecimiento":gTimb.get("dEst")})
    gOpeDE = _get_gOpeDE(moveId)
    data.update({"codigoSeguridadAleatorio":gOpeDE.get("dCodSeg")})
    data.update({"punto":gTimb.get("dPunExp")})
    data.update({"numero":gTimb.get("dNumDoc")})
    #data.update({"descripcion":12345})
    #data.update({"observacion":12345})
    gDatGralOpe = _get_gDatGralOpe(moveId)
    data.update({"fecha":gDatGralOpe.get("dFeEmiDE")})
    data.update({"tipoEmision":gOpeDE.get("iTipEmi")})

    gOpeCom = _get_gOpeCom(moveId)
    if gOpeCom.get("iTipTra") and gOpeCom.get("iTipTra") != None:
        data.update({"tipoTransaccion":int(gOpeCom.get("iTipTra") or 0) })
    data.update({"tipoImpuesto":gOpeCom.get("iTImp")})
    data.update({"moneda":gOpeCom.get("cMoneOpe")})
    if gOpeCom.get("cMoneOpe") != 'PRY':
        data.update({"condicionTipoCambio":gOpeCom.get("dCondTiCam")})
        data.update({"cambio":gOpeCom.get("dTiCam")})

    data.update({"cliente":_get_xmlgen_cliente(moveId)})
    if int(iTiDE or 0) == 1: # Factura
        data.update({"factura":_get_xmlgen_factura(moveId)})
        data.update({"condicion":_get_xmlgen_condicion(moveId)})
    elif int(iTiDE or 0) == 4: # Autofactura
        data.update({"autoFactura":_get_xmlgen_autofactura(moveId.partner_id, moveId.company_id)})
        data.update({"documentoAsociado":_get_xmlgen_documentoAsociado( moveId)})
        data.update({"condicion":_get_xmlgen_condicion(moveId)})
    elif int(iTiDE or 0) == 5:  # Nota de Credito
        data.update({"notaCreditoDebito":_get_xmlgen_notaCreditoDebito()})
        data.update({"condicion":_get_xmlgen_condicion(moveId)})
        data.update({"documentoAsociado":_get_xmlgen_documentoAsociado( moveId)})

    data.update({"items":_get_xmlgen_items( moveId)})
    

    #
    allData = {}
    allData.update({"empresa": moveId.company_id.vat.split("-")[0]})
    allData.update({"servicio": "de"})
    allData.update({"idCSC1": moveId.company_id.l10n_py_dnit_ws_idcsc1_test if moveId.company_id.l10n_py_dnit_ws_environment == 'testing' else moveId.company_id.l10n_py_dnit_ws_idcsc1_prod})
    allData.update({"idCSC2": moveId.company_id.l10n_py_dnit_ws_idcsc2_test if moveId.company_id.l10n_py_dnit_ws_environment == 'testing' else moveId.company_id.l10n_py_dnit_ws_idcsc2_prod})
    allData.update({"produccion": False if moveId.company_id.l10n_py_dnit_ws_environment == "testing" else True})
    allData.update({"params":params})
    allData.update({"data":data})
    options = {}
    if moveId.currency_id.name == 'PYG':
        options.update({"partialTaxDecimals": 0})
    elif moveId.currency_id.name == 'USD':
        options.update({"partialTaxDecimals": 2})
    allData.update({"options": options})
    _save_json_files(params,data,options)
    return allData