# -*- coding: utf-8 -*-

from odoo import fields, models, api

class PyResConfigSettingsIapFirebase(models.TransientModel):

    _inherit = 'res.config.settings'

    l10n_avatar_py_is_edi_test = fields.Boolean(related='company_id.l10n_avatar_py_is_edi_test', readonly=False)
    l10n_avatar_py_itipcont = fields.Selection(related="company_id.l10n_avatar_py_itipcont", readonly=False)

    # Timbrado
    l10n_avatar_py_authorization_code = fields.Char(
        related="company_id.partner_id.l10n_avatar_py_authorization_code", readonly=False)
    l10n_avatar_py_authorization_startdate = fields.Date(
        related="company_id.partner_id.l10n_avatar_py_authorization_startdate", readonly=False)
    l10n_avatar_py_authorization_enddate = fields.Date(
        related="company_id.partner_id.l10n_avatar_py_authorization_enddate", readonly=False)

    # Tipo de Regimen
    l10n_avatar_py_taxpayer_type = fields.Selection( 
        related="company_id.partner_id.l10n_avatar_py_taxpayer_type", readonly=False)
        
    # Retenciones
    l10n_avatar_py_tax_base_account_id = fields.Many2one(
        comodel_name='account.account',
        related='company_id.l10n_avatar_py_tax_base_account_id',
        readonly=False,
        domain=[('deprecated', '=', False)],
        string="Cuenta de base imponible",
        help="Cuenta que se establecerá en las líneas creadas para representar los importes de la base imponible.")        