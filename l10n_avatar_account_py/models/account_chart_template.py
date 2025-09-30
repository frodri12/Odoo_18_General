# -*- coding: utf-8 -*-

from odoo import models, api
from odoo.exceptions import ValidationError

class PyAccountChartTemplate(models.AbstractModel):

    _inherit = 'account.chart.template'

    def _load(self, template_code, company, install_demo,force_create=True):

        company.write({
            'country_id': self.env['res.country'].search([('code', '=', 'PY')]).id,
            'tax_calculation_rounding_method': 'round_per_line',
        })

        current_identification_type = company.partner_id.l10n_latam_identification_type_id
        try:
            company.partner_id.l10n_latam_identification_type_id = self.env.ref('l10n_avatar_account_py.py_ruc')
        except ValidationError:
            company.partner_id.l10n_latam_identification_type_id = current_identification_type

        res = super()._load(template_code, company, install_demo,force_create)
        return res

    def try_loading(self, template_code:str, company, install_demo=False, force_create=True):
        if not company:
            return
        if isinstance(company, int):
            company = self.env['res.company'].browse([company])
        if company.country_code == 'PY' and not company.chart_template:
            match = {
                self.env.ref('l10n_avatar_account_py.py_ruc'): 'py_base',
            }
            template_code = 'py_base'
        return super().try_loading(template_code, company, install_demo, force_create)
