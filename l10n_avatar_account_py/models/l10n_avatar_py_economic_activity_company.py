#

from odoo import fields, models

class PyEconomicActivityCompany(models.Model):

    _name = "l10n_avatar_py_economic_activity_company"
    _description = "l10n_avatar_py_economic_activity_company"

    l10n_avatar_py_economic_activity_id = fields.Many2one( 'l10n_avatar_py_economic_activity', string="Actividad Económica")
    company_id = fields.Many2one( 'res.company', string="Company")
    