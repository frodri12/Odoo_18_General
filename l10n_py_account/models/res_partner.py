# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from stdnum.util import clean
import stdnum.py.ruc
from stdnum.exceptions import InvalidLength, InvalidChecksum
from stdnum.exceptions import ValidationError as ValidationErrorStdnum
import curses.ascii
import re
import logging

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

class ResPartner(models.Model):

    _inherit = 'res.partner'

    l10n_py_dnit_responsibility_type_id = fields.Many2one(
        'l10n_py.dnit.responsibility.type', string='DNIT Responsibility Type', index='btree_not_null', 
        help='Tipo de responsabilidad que una persona o entidad jurídica podría tener. Impactan en algunas operaciones.')

    ###
    ### Constraints
    ###
    @api.constrains('vat', 'l10n_latam_identification_type_id')
    def check_vat(self):
        # Dado que validamos más documentos que el RUC, ampliamos este método para su procesamiento.
        # NOTA: Por el momento, también incluimos la validación del RUC
        #       aquí, ya que ampliamos los mensajes de error para que sean más intuitivos.
        l10n_py_partners = self.filtered(lambda p: p.l10n_latam_identification_type_id.l10n_py_dnit_code or p.country_code == 'PY')
        l10n_py_partners.l10n_py_identification_validation()
        return super(ResPartner, self - l10n_py_partners).check_vat()

    def l10n_py_identification_validation(self):
        for rec in self.filtered('vat'):
            if not rec.l10n_latam_identification_type_id.l10n_py_dnit_code in ['0']:
                continue

            if rec.vat.split("-").__len__() > 1:  # El RUC viene con el separador
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
                #except Exception as error:
                #    raise ValidationError(repr(error))
            else:
                no_digit = str(rec.vat) + "-" + str(calc_check_digit(str(rec.vat)))
                si_digit = str(rec.vat)[:-1] + "-" + str(calc_check_digit(str(rec.vat)[:-1]))
                msg = _("El formato del RUC es incorrecto. [Posibles valores: %s o %s]", no_digit, si_digit)
                raise ValidationError(msg)

    l10n_py_vat = fields.Char(
        compute='_compute_l10n_py_vat', string="VAT", 
        help='Campo calculado que devuelve el RUC o nada si este no está configurado')
    l10n_py_formatted_vat = fields.Char(
        compute='_compute_l10n_py_formatted_vat', string="Formatted VAT", 
        help='Campo calculado que convertirá el número del RUC al formato {número:8}-{número_de_validación:1}')

    @api.depends('vat', 'l10n_latam_identification_type_id')
    def _compute_l10n_py_vat(self):
        """ We add this computed field that returns RUC (VAT PY) or nothing if this one is not set for the partner.
        This Validation can be also done by calling ensure_vat() method that returns the RUC (VAT PY) or error if this
        one is not found """
        recs_py_vat = self.filtered(lambda x: x.l10n_latam_identification_type_id.l10n_py_dnit_code == '0' and x.vat)
        for rec in recs_py_vat:
            rec.l10n_py_vat = compact(rec.vat)
        remaining = self - recs_py_vat
        remaining.l10n_py_vat = False

    @api.depends('l10n_py_vat')
    def _compute_l10n_py_formatted_vat(self):
        """ This will add some dash to the RUC number (VAT PY) in order to show in his natural format:
        {number}-{validation_number} """
        recs_py_vat = self.filtered('l10n_py_vat')
        for rec in recs_py_vat:
            try:
                rec.l10n_py_formatted_vat = format(rec.l10n_py_vat)
            except Exception as error:
                rec.l10n_py_formatted_vat = rec.l10n_py_vat
        remaining = self - recs_py_vat
        remaining.l10n_py_formatted_vat = False

    ###
    ### Override
    ###
    @api.model
    def _commercial_fields(self):
        return super()._commercial_fields() + ['l10n_py_dnit_responsibility_type_id']

    ###
    ###
    ###
    def ensure_vat(self):
        # Este método es un ayudante que devuelve el número de RUC si éste está definido, 
        # si no, se genera un Error.

        # El RUC no es un campo obligatorio, pero para algunas operaciones en Paraguay sí lo es, 
        # por ejemplo, validar una factura electrónica, crear un informe, etc.

        # Este método se puede utilizar para validar si el RUC está correctamente definido.
        self.ensure_one()
        if not self.l10n_py_vat:
            raise UserError(_('No RUC configured for partner [%i] %s', self.id, self.name))
        return self.l10n_py_vat

    def _get_id_number_sanitize(self):
        # Depurar el número de identificación.
        # Devolver los dígitos/valor del número de identificación.
        # Si no se ha definido el número de RUC, devolver 0.
        self.ensure_one()
        if not self.vat:
            return 0
        if self.l10n_latam_identification_type_id.l10n_py_dnit_code in ['0']:
            res = int(compact(self.vat))
        else:
            id_number = re.sub('[^0-9]', '', self.vat)
            res = int(id_number)
        return res

    ###########################
    l10n_py_house = fields.Char("House")
    l10n_py_district_id = fields.Many2one("l10n_py_district")
    l10n_py_city_id = fields.Many2one("l10n_py_city")

    @api.onchange('country_id','l10n_py_city_id')
    def _onchange_city(self):
        if self.country_id.code == 'PY' and self.l10n_py_city_id.country_id.code == 'PY' :
            self.write({'city': self.l10n_py_city_id.name,})
            
    ###################
    @api.model
    def default_get(self,fields_list):
        res = super().default_get(fields_list)
        res.update(
            {'country_id':self.env['res.country'].search([('code', '=', 'PY')], limit=1).id}
        )
        res.update({'lang':self.env.lang})
        return res

        
    l10n_py_dnit_auth_code = fields.Char("Numero de Timbrado")
    l10n_py_dnit_auth_startdate = fields.Date("Fecha de Inicio del Timbrado")
    l10n_py_dnit_auth_enddate = fields.Date("Fecha de FIn del Timbrado")
    
    l10n_py_dnit_self_number = fields.Char("Número de Constancia")
    l10n_py_dnit_self_control = fields.Char("Número de Control")
    l10n_py_dnit_self_end_date = fields.Date("Fecha de Validez")
