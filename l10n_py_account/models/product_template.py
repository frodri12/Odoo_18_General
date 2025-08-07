#

from odoo import fields, models, _
from odoo.exceptions import UserError
import re


class ProductTemplate(models.Model):

    _inherit = 'product.template'

    l10n_py_ncm_code = fields.Char('NCM Code', copy=False, help='Código según el Nomenclador Común del MERCOSUR')

    def _check_l10n_ar_ncm_code(self):
        self.ensure_one()
        if self.l10n_py_ncm_code and not re.match(r'^[0-9\.]+$', self.l10n_py_ncm_code):
            raise UserError(_('Parece que el producto "%s" no tiene un código NCM válido.\n\nEstablezca un código NCM válido para continuar.'
                , self.display_name))
