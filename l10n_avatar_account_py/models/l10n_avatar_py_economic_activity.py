#

from odoo import fields, models

class PyEconomicActivity(models.Model):
    _name = "l10n_avatar_py_economic_activity"
    _description = "l10n_avatar_py_economic_activity"

    name = fields.Char(string="Nombre")
    code = fields.Char(string="Código")
    active = fields.Boolean()

    def _get_sifen_ActEco( self):
        return (
            { 'cActEco': self.code},
            { 'dDesActEco': self.name},
        )
    