# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api, _

class AccountFiscalPosition(models.Model):

    _inherit = 'account.fiscal.position'

    l10n_ar_afip_responsibility_type_ids = fields.Many2many(
        'l10n_py.dnit.responsibility.type', 'l10n_py_dnit_reponsibility_type_fiscal_pos_rel',
        string='Tipos de responsabilidad')

    def _get_fpos_ranking_functions(self, partner):
        if self.env.company.country_id.code != "PY":
            return super()._get_fpos_ranking_functions(partner)
        return [
            ('l10n_py_dnit_responsibility_type_id', lambda fpos: (
                partner.l10n_py_dnit_responsibility_type_id in fpos.l10n_py_dnit_responsibility_type_ids
            ))
        ] + super()._get_fpos_ranking_functions(partner)