# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class L10nPyDnitResponsibilityType(models.Model):

    _name = 'l10n_py.dnit.responsibility.type'
    _description = 'Tipo de responsabilidad'
    _order = 'sequence'

    name = fields.Char(required=True, index='trigram')
    sequence = fields.Integer()
    code = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [('name', 'unique(name)', 'Name must be unique!'),
                        ('code', 'unique(code)', 'Code must be unique!')]