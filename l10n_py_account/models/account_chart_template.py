# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, _
from odoo.exceptions import ValidationError
from odoo.addons.account.models.chart_template import template


class AccountChartTemplate(models.AbstractModel):
    _inherit = 'account.chart.template'

    def _load(self, template_code, company, install_demo,force_create=True):
        coa_responsibility = self._get_py_responsibility_match(template_code)
        if coa_responsibility:
            company.write({
                'l10n_py_dnit_responsibility_type_id': coa_responsibility.id,
                'country_id': self.env['res.country'].search([('code', '=', 'PY')]).id,
                'tax_calculation_rounding_method': 'round_per_line',    ### 'round_globally',
            })

            current_identification_type = company.partner_id.l10n_latam_identification_type_id
            try:
                # set RUC identification type (which is the paraguayan vat) in the created company partner instead of
                # the default VAT type.
                company.partner_id.l10n_latam_identification_type_id = self.env.ref('l10n_py_account.it_ruc')
            except ValidationError:
                # put back previous value if we could not validate the RUC
                company.partner_id.l10n_latam_identification_type_id = current_identification_type

        res = super()._load(template_code, company, install_demo,force_create)

        return res

    @api.model
    def _get_py_responsibility_match(self, chart_template):
        match = {
            'py_base': self.env.ref('l10n_py_account.res_IVARI'),
        }
        return match.get(chart_template)

    def try_loading(self, template_code:str, company, install_demo=False, force_create=True):
        # During company creation load template code corresponding to the DNIT Responsibility
        if not company:
            return
        if isinstance(company, int):
            company = self.env['res.company'].browse([company])
        if company.country_code == 'PY' and not company.chart_template:
            match = {
                self.env.ref('l10n_py_account.it_ruc'): 'py_base',
            }
            #template_code = match.get(company.l10n_py_dnit_responsibility_type_id, template_code)
            template_code = 'py_base'
        return super().try_loading(template_code, company, install_demo, force_create)