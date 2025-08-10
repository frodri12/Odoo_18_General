# -*- coding: utf-8 -*-

import idna
from odoo import fields, models, api, _
import logging
from stdnum.util import clean
import curses.ascii
from stdnum.exceptions import InvalidLength, InvalidChecksum
from stdnum.exceptions import ValidationError as ValidationErrorStdnum
from odoo.exceptions import ValidationError
import stdnum.py.ruc

_logger = logging.getLogger(__name__)

ADDRESS_FIELDS = (
    'street', 'l10n_py_house', 'street2', 
    'zip', 'city', 'state_id', 'l10n_py_district_id', 
    'l10n_py_city_id', 'country_id')

## Funciones par ala validacion del RUC, reemplazand stdnum.py.ruc

# Convierte el número a la representación mínima.
def compact(number):
    # Esto elimina el número de separadores válidos y elimina 
    #   los espacios en blanco circundantes.
    return clean(number, ' -').upper().strip()
        
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

# Reformatear el número al formato de presentación estándar.
def format(number):
    number = compact(number)
    return '-'.join([number[:-1], number[-1]])

class PyResPartner(models.Model):

    _inherit = 'res.partner'

    l10n_py_house = fields.Char(string="House")
    l10n_py_district_id = fields.Many2one(comodel_name="l10n_py_state_district", string="District")
    l10n_py_city_id = fields.Many2one(comodel_name="l10n_py_district_city", string="PY City")

    @api.model
    def default_get(self,fields_list):
        res = super().default_get(fields_list)
        country = self.env['res.country'].search([('code', '=', 'PY')], limit=1).id
        state = self.env['res.country.state'].search([('code', '=', '1'), ('country_id', '=', country)], limit=1).id
        district = self.env['l10n_py_state_district'].search([('state_id', '=', state)], limit=1).id
        city = self.env['l10n_py_district_city'].search([('district_id', '=', district)], limit=1).id
        res.update({'country_id':country})
        res.update({'state_id':state})
        res.update({'l10n_py_district_id':district})
        res.update({'l10n_py_city_id':city})
        res.update({'lang':self.env.lang})
        return res

    @api.onchange('l10n_py_district_id')
    def _onchange_district_id(self):
        if self.l10n_py_district_id.state_id and self.state_id != self.l10n_py_district_id.state_id:
            self.state_id = self.l10n_py_district_id.state_id

    @api.onchange('l10n_py_city_id')
    def _onchange_city_id(self):
        if self.l10n_py_city_id.district_id and self.l10n_py_district_id != self.l10n_py_city_id.district_id:
            self.l10n_py_district_id = self.l10n_py_city_id.district_id

    @api.onchange('l10n_py_city_id')
    def _onchange_city(self):
        if self.country_id.code == 'PY':
            if self.l10n_py_city_id:
                #self.write({'city': self.l10n_py_city_id.name})
                self.city = self.l10n_py_city_id.name
            else:
                #self.write({'city': False})
                self.city = None

    ######

    @api.constrains('vat', 'l10n_latam_identification_type_id')
    def check_vat(self):
        partners = self.filtered(lambda p: p.l10n_latam_identification_type_id.l10n_py_dnit_document_type or p.country_code == 'PY')
        partners.l10n_py_identification_validation()
        return super(PyResPartner, self - partners).check_vat()

    def l10n_py_identification_validation(self):
        for rec in self.filtered('vat'):
            if not rec.l10n_latam_identification_type_id.l10n_py_dnit_document_type in [99]: #RUC
                continue
            if rec.vat.split("-").__len__() > 1:  # El RUC viene con el guion
                try:
                    if not is_valid(rec.vat):
                        no_digit = rec.vat.split("-")[0]
                        raise ValidationError("The RUC number is invalid [%s]" % str(calc_check_digit(no_digit)))
                except stdnum.py.ruc.InvalidChecksum:
                    no_digit = rec.vat.split("-")[0]
                    #msg = _("El digito de control del RUC %s es invalido [%s]", rec.vat, str(no_digit) + "-" + str(calc_check_digit( no_digit )))
                    msg = _("The RUC verification digit is invalid.\n\tA possible value could be %s", str(calc_check_digit(no_digit)))
                    raise ValidationError(msg)
                except stdnum.py.ruc.InvalidLength:
                    raise ValidationError("Invalid length for the RUC")
                except stdnum.py.ruc.InvalidFormat:
                    raise ValidationError("Only numbers are allowed for the RUC")
            else:
                no_digit = str(rec.vat) + "-" + str(calc_check_digit(str(rec.vat)))
                si_digit = str(rec.vat)[:-1] + "-" + str(calc_check_digit(str(rec.vat)[:-1]))
                msg = _("The RUC format is incorrect.")
                raise ValidationError(msg)
