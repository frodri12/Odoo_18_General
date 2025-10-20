# -*- coding: utf-8 -*-

from odoo import fields, models, api

class PyResCompany(models.Model):

    _inherit = "res.company"

    # Direccion
    municipality_id = fields.Many2one(
        comodel_name='l10n_avatar_py_municipality', string="Municipio", 
        compute='_compute_address', inverse='_inverse_compute_municipality_id')
    city_id = fields.Many2one(
        comodel_name='l10n_avatar_py_city', string="Ciudad", 
        compute='_compute_address', inverse='_inverse_compute_city_id')
    external_number = fields.Integer(
        string="Casa", compute='_compute_address', inverse='_inverse_compute_external_number')

    # Actividades Economicas
    l10n_avatar_py_economic_activity_ids = fields.Many2many(
        'l10n_avatar_py_economic_activity', 'l10n_avatar_py_economic_activity_company_rel',
        'company_id', 'economic_activity_id'
    )

    # Facturacion electronica
    l10n_avatar_py_is_edi_test = fields.Boolean(string="Entorno de TEST", default=True)
    l10n_avatar_py_itipcont = fields.Selection([
        ('1', 'Persona física'), ('2', 'Persona jurídica')
    ], string="Tipo de contribuyente", default='2')

    # Retenciones
    l10n_avatar_py_tax_base_account_id = fields.Many2one(
        comodel_name='account.account',
        domain=[('deprecated', '=', False)],
        string="Cuenta de base imponible",
        help="Cuenta que se establecerá en las líneas creadas para representar los importes de la base imponible.")
        
    def _inverse_compute_municipality_id(self):
        for company in self:
            company.partner_id.municipality_id = company.municipality_id

    def _inverse_compute_city_id(self):
        for company in self:
            company.partner_id.city_id = company.city_id

    def _inverse_compute_external_number(self):
        for company in self:
            company.partner_id.external_number = company.external_number

    def _get_company_address_field_names(self):
        return [
            'street', 
            'external_number', 
            'street2', 
            'zip', 
            'city', 
            'state_id', 
            'municipality_id', 
            'city_id', 
            'country_id'
        ]

    def _localization_use_documents(self):
        self.ensure_one()
        return self.account_fiscal_country_id.code == "PY" or super()._localization_use_documents()

    @api.onchange('country_id')
    def onchange_country(self):
        for rec in self.filtered(lambda x: x.country_id.code == "PY"):
            rec.tax_calculation_rounding_method = 'round_per_line'

    def _get_sifen_data( self):
        # D013 = iTImp = Tipo de impuesto afectado = 1= IVA, 2= ISC 3=Renta 4=Ninguno 5=IVA - Renta
        iTImp_D013 = 1 #  Dato a definir en la compania (config)
        #
        return {
            'iTImp_D013': iTImp_D013,
		}

    def _get_sifen_gActEco(self):
        gActEco = []
        for rec in self.l10n_avatar_py_economic_activity_ids:
            gActEco.append(rec._get_sifen_ActEco())
        return gActEco
