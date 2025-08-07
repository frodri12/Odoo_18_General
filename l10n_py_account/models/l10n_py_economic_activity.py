# -*- coding: utf-8 -*-

from odoo import models, fields

class L10npyEconomicActivity(models.Model):
    _name = 'l10n_py.economic.activity'
    _description = 'Actividad económica'
    _rec_name = 'name'
    _order = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    code = fields.Char(
        string='Code',
        required=True,
        help='Código de la actividad económica',
    )
    name = fields.Char(
        string='Name',
        required=True,
        help='Nombre de la actividad económica',
    )
    #description = fields.Text(string='Description',help='Description of the economic activity',)
    active = fields.Boolean(
        string='Active',
        default=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        help='Empresa asociada a la actividad económica',
    )

#    def _get_l10n_py_dnit_ws_economic_avtivity( self):
#        eco = {}
#        eco.update({"codigo": self.code}) #D131
#        eco.update({"descripcion": self.name}) #D132
#        return eco