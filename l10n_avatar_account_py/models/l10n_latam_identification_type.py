# -*- coding: utf-8 -*-

from odoo import models, fields

class PyL10nLatamIdentificationType(models.Model):

    _inherit = "l10n_latam.identification.type"

    l10n_avatar_py_code = fields.Integer("EDI Document Type")
