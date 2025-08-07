# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.tools.float_utils import float_round

import logging

_logger = logging.getLogger(__name__)

class l10nPyAccountMoveLine(models.Model):

    _inherit = 'account.move.line'

    #l10n_py_price_unit_iva0  = fields.Float(compute='_l10n_py_compute_totals', store=True)
    #l10n_py_price_unit_iva5  = fields.Float(compute='_l10n_py_compute_totals', store=True)
    #l10n_py_price_unit_iva10 = fields.Float(compute='_l10n_py_compute_totals', store=True)

    l10n_py_base_grav_exe = fields.Float(compute='_l10n_py_compute_totals', store=True)
    l10n_py_base_grav_tax5 = fields.Float(compute='_l10n_py_compute_totals', store=True)
    l10n_py_base_grav_tax10 = fields.Float(compute='_l10n_py_compute_totals', store=True)

    @api.depends('quantity', 'discount', 'price_unit', 'tax_ids', 'currency_id')
    def _l10n_py_compute_totals(self):
        #AccountTax = self.env['account.tax']
        for line in self:
            if line.display_type not in ('product', 'cogs'):
                continue
            #
            AccountTax = line.tax_ids
            #
            dTotOpeItem = line.price_unit * line.quantity
            if line.discount and line.discount > 0:
                dTotOpeItem = (line.price_unit * ( 1 - (line.discount / 100))) * line.quantity

            ivaTipo = 1
            ivaBase = AccountTax.l10n_py_tax_base
            ivaAmount = AccountTax.amount
            if ivaBase < 100 and ivaBase > 0:
                ivaTipo = 4
                ivaAmount = ivaAmount * 100 / ivaBase
            if ivaAmount == 0:
                ivaTipo = 3
                ivaAmount = 0
            #
            line.l10n_py_base_grav_exe = 0.0
            line.l10n_py_base_grav_tax5 = 0.0
            line.l10n_py_base_grav_tax10 = 0.0

            precision_rounding = line.currency_id.rounding
            rounding_method = line.company_id.tax_calculation_rounding_method

            #
            if ivaTipo == 3:
                line.l10n_py_base_grav_exe = dTotOpeItem
            elif ivaTipo == 1 and ivaAmount == 5:
                line.l10n_py_base_grav_tax5 = dTotOpeItem
            elif ivaTipo == 1 and ivaAmount == 10:
                line.l10n_py_base_grav_tax10 = dTotOpeItem
            elif ivaTipo == 4:
                line.l10n_py_base_grav_exe = (100 * dTotOpeItem * (100 - ivaBase)) / (10000 + (ivaAmount * ivaBase))
                if rounding_method== 'round_per_line':
                    line.l10n_py_base_grav_exe = float_round(  line.l10n_py_base_grav_exe,  precision_rounding=precision_rounding)
                if ivaAmount == 5:
                    line.l10n_py_base_grav_tax5 = (100 * dTotOpeItem * ivaBase) / (10000 + (ivaAmount * ivaBase))
                    if rounding_method== 'round_per_line':
                        line.l10n_py_base_grav_tax5 = float_round(  line.l10n_py_base_grav_tax5,  precision_rounding=precision_rounding)
                if ivaAmount == 10:
                    line.l10n_py_base_grav_tax10 = (100 * dTotOpeItem * ivaBase) / (10000 + (ivaAmount * ivaBase))
                    if rounding_method== 'round_per_line':
                        line.l10n_py_base_grav_tax10 = float_round(  line.l10n_py_base_grav_tax10,  precision_rounding=precision_rounding)
                    
                    



