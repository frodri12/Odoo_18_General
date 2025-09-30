# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import stdnum.py.ruc
from stdnum.util import clean
import curses.ascii
from stdnum.exceptions import InvalidLength, InvalidChecksum
from stdnum.exceptions import ValidationError as ValidationErrorStdnum

ADDRESS_FIELDS = (
    'street', 'external_number', 'street2', 
    'zip', 'city', 'state_id', 'municipality_id', 
    'city_id', 'country_id')

# Calcular el dígito de control.        
def calc_check_digit(number):
    # El número pasado no debe incluir el dígito de control.
    v_numero_al = ""
    v_total = 0
    for i, n in enumerate(number):
        v_numero_al += str(n) if n.isdigit() else str(ord(curses.ascii.ascii(n.upper())))
    for i, n in enumerate(reversed(v_numero_al)):
        v_total += (int(n) * ((i % 10) + 2))
    return 11 - (v_total % 11) if (v_total % 11) > 1 else 0

# Convierte el número a la representación mínima.
def compact(number):
    # Esto elimina el número de separadores válidos y elimina 
    #   los espacios en blanco circundantes.
    return clean(number, ' -').upper().strip()

# Comprueba si el número es un RUC de Paraguay válido.        
def validate(number):
    # Esto verifica la longitud, el formato y el dígito de control.
    number = compact(number)
    if len(number) > 9:
        return -1 # raise InvalidLength()
    if str(number[-1]) != str(calc_check_digit(number[:-1])):
        return -2 # raise InvalidChecksum()
    return number

# Verifique si el número es un número RUC de Paraguay válido.
def is_valid(number):
    n = 0
    try:
        n = validate(number)
        if n == -1:
            raise InvalidLength()
        elif n == -2:
            raise InvalidChecksum()
        #return bool(validate(number))
        return True
    except ValidationErrorStdnum:
        return False

class ResPartner(models.Model):

    _inherit = "res.partner"

    # Direccion
    municipality_id = fields.Many2one(comodel_name='l10n_avatar_py_municipality', string="Municipio")
    city_id = fields.Many2one(comodel_name='l10n_avatar_py_city', string="Ciudad")
    external_number = fields.Integer(string="Casa")

    # Timbrado
    l10n_avatar_py_authorization_code = fields.Char(string="Timbrado")
    l10n_avatar_py_authorization_startdate = fields.Date(string="Fecha inicio de Timbrado")
    l10n_avatar_py_authorization_enddate = fields.Date(string="Fecha de fin de Timbrado")

    # Tipo de Regimen
    l10n_avatar_py_taxpayer_type = fields.Selection([
        ('0', 'Sin Asignar'),
        ('1', 'Régimen de turismo'),
        ('2', 'Importador'),
        ('3', 'Exportador'),
        ('4', 'Maquila'),
        ('5', 'Ley N° 60/90'),
        ('6', 'Régimen del Pequeño Productor'),
        ('7', 'Régimen del Mediano Productor'),
        ('8', 'Régimen Contable'),
    ], string="Tipo de Regimen", default="0")

    # Retenciones
    l10n_avatar_py_partner_tax_ids = fields.One2many(
        'l10n_avatar_py_partner_tax', 'partner_id', 'Impuestos de retención',
    )
    
    # Constancia de No Contribuyente
    l10n_avatar_py_taxpayer_number = fields.Char(string="Nº de Constancia")
    l10n_avatar_py_taxpayer_control = fields.Char(string="Nº de Control")
    l10n_avatar_py_taxpayer_startdate = fields.Date(string="Fecha de inicio de constancia")
    l10n_avatar_py_taxpayer_enddate = fields.Date(string="Fecha fin de constancia")


    @api.model
    def default_get(self,fields_list):
        res = super().default_get(fields_list)
        country = self.env['res.country'].search([('code', '=', 'PY')], limit=1).id
        state = self.env['res.country.state'].search([('code', '=', '1'), ('country_id', '=', country)], limit=1).id
        municipality = self.env['l10n_avatar_py_municipality'].search([('state_id', '=', state)], limit=1).id
        city = self.env['l10n_avatar_py_city'].search([('state_id', '=', state)], limit=1).id
        res.update({'country_id': country})
        res.update({'state_id': state})
        res.update({'municipality_id': municipality})
        res.update({'city_id': city})
        res.update({'lang':self.env.lang})
        return res

    # Validacion del RUC
    @api.constrains('vat', 'l10n_latam_identification_type_id')
    def check_vat(self):
        partners = self.filtered(lambda p: p.l10n_latam_identification_type_id.l10n_avatar_py_code or p.country_code == 'PY')
        partners.l10n_avatar_py_identification_validation()
        return super(ResPartner, self - partners).check_vat()

    def l10n_avatar_py_identification_validation(self):
        for rec in self.filtered('vat'):
            if not rec.l10n_latam_identification_type_id.l10n_avatar_py_code in [99]:
                continue
            if rec.vat.split("-").__len__() > 1: # El RUC viene con el separador
                try:
                    if not is_valid(rec.vat):
                        raise ValidationError("El número de RUC es inválido")
                except stdnum.py.ruc.InvalidChecksum:
                    no_digit = rec.vat.split("-")[0]
                    msg = _("El digito de control del RUC %s es invalido [%s]", rec.vat, str(no_digit) + "-" + str(calc_check_digit( no_digit )))
                    raise ValidationError(msg)
                except stdnum.py.ruc.InvalidLength:
                    raise ValidationError("Longitud no válida para el RUC [%s]" % rec.vat)
                except stdnum.py.ruc.InvalidFormat:
                    raise ValidationError("Solo se permiten números para el RUC [%s]" % rec.vat)
            else:
                no_digit = str(rec.vat) + "-" + str(calc_check_digit(str(rec.vat)))
                si_digit = str(rec.vat)[:-1] + "-" + str(calc_check_digit(str(rec.vat)[:-1]))
                msg = _("El formato del RUC es incorrecto. [Posibles valores: %s o %s]", no_digit, si_digit)
                raise ValidationError(msg)

