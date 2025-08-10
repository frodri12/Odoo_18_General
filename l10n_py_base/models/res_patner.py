# -*- coding: utf-8 -*-

import idna
from odoo import fields, models, api, _
import logging

_logger = logging.getLogger(__name__)

ADDRESS_FIELDS = (
    'street', 'l10n_py_house', 'street2', 
    'zip', 'city', 'state_id', 'l10n_py_district_id', 
    'l10n_py_city_id', 'country_id')

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
