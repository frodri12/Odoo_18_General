
from odoo import _, fields, models
from odoo.exceptions import UserError

class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    l10n_py_custom_report_payment = fields.Boolean(related='company_id.l10n_py_custom_report_payment', readonly=False)

