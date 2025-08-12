# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
import logging

_logger = logging.getLogger(__name__)

class PyResCompany(models.Model):

    _inherit = "res.company"

    l10n_py_house = fields.Char(
        string="House", compute='_compute_address', inverse='_inverse_compute_house')
    l10n_py_district_id = fields.Many2one(
        comodel_name="l10n_py_state_district", string="District", 
        compute='_compute_address', inverse='_inverse_compute_district')
    l10n_py_city_id = fields.Many2one(
        comodel_name="l10n_py_district_city", string="PY City", 
        compute='_compute_address', inverse='_inverse_compute_city')

    l10n_py_regime_type = fields.Selection([
            ('0','Sin Asignar'),('1','Regimen de Turismo'),('2','Importador'),
            ('3','Exportador'),('4','Maquila'),('5','Ley N° 60/90'),
            ('6','Regimen del Pequeño Productor'),('7','Regimen del Mediano Productor'),
            ('8','Regimen Contable'),
        ], string="Regime Type", default='0')

    l10n_py_economic_activity_ids = fields.One2many(
        comodel_name="l10n_py_economic_activity", inverse_name="company_id",
        string="Economic activity")

    def _inverse_compute_house(self):
        for company in self:
            company.partner_id.l10n_py_house = company.l10n_py_house

    def _inverse_compute_district(self):
        for company in self:
            company.partner_id.l10n_py_district_id = company.l10n_py_district_id

    def _inverse_compute_city(self):
        for company in self:
            company.partner_id.l10n_py_city_id = company.l10n_py_city_id

    def _get_company_address_field_names(self):
        # Devuelve una lista de campos de direcciones para que coincidan con los campos de dirección de la empresa.
        # Los campos tienen la misma etiqueta en ambos modelos.
        return [
            'street', 'l10n_py_house', 'street2', 
            'city', 'zip', 'state_id', 'l10n_py_district_id', 
            'l10n_py_city_id', 'country_id']

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
