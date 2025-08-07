
from odoo import _, fields, models
from odoo.exceptions import UserError

class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    l10n_py_dnit_ws_environment = fields.Selection(related='company_id.l10n_py_dnit_ws_environment', readonly=False)

    l10n_py_regime_type_id = fields.Many2one(related='company_id.l10n_py_regime_type_id', readonly=False)

    l10n_py_dnit_ws_idcsc1_prod = fields.Char( related='company_id.l10n_py_dnit_ws_idcsc1_prod' )
    l10n_py_dnit_ws_idcsc2_prod = fields.Char( related='company_id.l10n_py_dnit_ws_idcsc2_prod' )
    l10n_py_dnit_ws_idcsc1_test = fields.Char( related='company_id.l10n_py_dnit_ws_idcsc1_test' )
    l10n_py_dnit_ws_idcsc2_test = fields.Char( related='company_id.l10n_py_dnit_ws_idcsc2_test' )
     