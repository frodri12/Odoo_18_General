# -*- coding: utf-8 -*-

from odoo import fields, models, api, _

import logging
_logger = logging.getLogger(__name__)

class PyAccountMoveLine(models.Model):

    _inherit = 'account.move.line'

    # For reports
    l10n_avatar_py_amount_base_exempt = fields.Monetary(compute='_onchange_py_amounts', store=True)
    l10n_avatar_py_amount_base_5 = fields.Monetary(compute='_onchange_py_amounts', store=True)
    l10n_avatar_py_amount_base_10 = fields.Monetary(compute='_onchange_py_amounts', store=True)
    l10n_avatar_py_tax_base_5 = fields.Monetary(compute='_onchange_py_amounts', store=True)
    l10n_avatar_py_tax_base_10 = fields.Monetary(compute='_onchange_py_amounts', store=True)
    l10n_avatar_py_amount_currency_base_exempt = fields.Monetary(
        string="Importe Exento",compute='_onchange_py_amounts', 
        store=True, currency_field='company_currency_id')
    l10n_avatar_py_amount_currency_base_5 = fields.Monetary(
        string="Importe Gravado 5%",compute='_onchange_py_amounts', 
        store=True, currency_field='company_currency_id')
    l10n_avatar_py_amount_currency_base_10 = fields.Monetary(
        string="Importe Gravado 10%",compute='_onchange_py_amounts', 
        store=True, currency_field='company_currency_id')
    l10n_avatar_py_tax_currency_base_5 = fields.Monetary(
        string="IVA 5%",compute='_onchange_py_amounts', 
        store=True, currency_field='company_currency_id')
    l10n_avatar_py_tax_currency_base_10 = fields.Monetary(
        string="IVA 10%",compute='_onchange_py_amounts', 
        store=True, currency_field='company_currency_id')

    # For reports
    @api.depends('quantity', 'discount', 'price_unit', 'tax_ids', 'currency_id', 'parent_state')
    def _onchange_py_amounts(self):
        for rec in self:
            rec._onchange_py_amounts_unique()



    def _onchange_py_amounts_unique(self):
        if self.sequence > 9999:
            self.l10n_avatar_py_amount_base_exempt = 0.0
            self.l10n_avatar_py_amount_base_5 = 0.0
            self.l10n_avatar_py_amount_base_10 = 0.0
            self.l10n_avatar_py_tax_base_5 = 0.0
            self.l10n_avatar_py_tax_base_10 = 0.0
        else:
            rec = self._get_sifen_data()
            self.l10n_avatar_py_amount_base_exempt = rec.get('dBasExe_E737') or 0.0
            if rec.get('iAfecIVA_E731') == 1:
                self.l10n_avatar_py_amount_base_5 = rec.get('dTotOpeItem_EA008') if rec.get('dTasaIVA_E734') == 5 else 0.0
                self.l10n_avatar_py_amount_base_10 = rec.get('dTotOpeItem_EA008') if rec.get('dTasaIVA_E734') == 10 else 0.0
            else:
                dBasGravIVA_E735_f = float(rec.get('dBasGravIVA_E735') or 0.0) 
                dLiqIVAItem_E736_f = float(rec.get('dLiqIVAItem_E736') or 0.0)
                self.l10n_avatar_py_amount_base_5 = (dBasGravIVA_E735_f + dLiqIVAItem_E736_f)  if rec.get('dTasaIVA_E734') == 5 else 0.0
                self.l10n_avatar_py_amount_base_10 = (dBasGravIVA_E735_f + dLiqIVAItem_E736_f)  if rec.get('dTasaIVA_E734') == 10 else 0.0
            self.l10n_avatar_py_tax_base_5 = rec.get('dLiqIVAItem_E736')  if rec.get('dTasaIVA_E734') == 5 else 0.0
            self.l10n_avatar_py_tax_base_10 = rec.get('dLiqIVAItem_E736') if rec.get('dTasaIVA_E734') == 10 else 0.0
        #
        divisor = self.move_id.invoice_currency_rate
        if not divisor or divisor == 0.0:
            divisor = 1.0
        self.l10n_avatar_py_amount_currency_base_exempt = self.l10n_avatar_py_amount_base_exempt / divisor
        self.l10n_avatar_py_amount_currency_base_5 = self.l10n_avatar_py_amount_base_5 / divisor
        self.l10n_avatar_py_amount_currency_base_10 = self.l10n_avatar_py_amount_base_10 / divisor
        self.l10n_avatar_py_tax_currency_base_5 = self.l10n_avatar_py_tax_base_5 / divisor
        self.l10n_avatar_py_tax_currency_base_10 = self.l10n_avatar_py_tax_base_10 / divisor
        

    def _get_sifen_data(self):
        iTImp_D013 = self.company_id._get_sifen_data().get('iTImp_D013')
        # E711 = dCantProSer = Cantidad del producto y/o servicio
        dCantProSer_E711 = self.quantity
        # E721 = dPUniProSer = Precio unitario del producto y/o servicio (incluidos impuestos)
        dPUniProSer_E721 = self.price_unit
        # EA002 = dDescItem = Descuento particular sobre el precio unitario por ítem (incluidos impuestos)
        dDescItem_EA002 = dPUniProSer_E721 * self.discount / 100.0
        # EA004 = dDescGloItem = Descuento global sobre el precio unitario por ítem (incluidos impuestos)
        dDescGloItem_EA004 = 0.0
        # EA006 = dAntPreUniIt = Anticipo particular sobre el precio unitario por ítem (incluidos impuestos)
        dAntPreUniIt_EA006 = 0.0
        # EA007 = dAntGloPreUniIt = Anticipo global sobre el precio unitario por ítem (incluidos impuestos)
        dAntGloPreUniIt_EA007 = 0.0
        # EA008 = dTotOpeItem = Valor total de la operación por ítem
        #   Cálculo para IVA, Renta, ninguno, IVA - Renta:
        #      Si D013 = 1, 3, 4 o 5 (afectado al IVA, Renta, ninguno, IVA - Renta),
        #      entonces EA008 corresponde al cálculo aritmético:
        #        (E721 (Precio unitario) – EA002 (Descu1ento particular) – EA004 (Descuento global) – EA006 (Anticipo particular) – EA007 (Anticipo global)) * E711(cantidad)
        #   Cálculo para Autofactura (C002=4):
        #      E721*E711
        dTotOpeItem_EA008 = 0.0
        if iTImp_D013 != 2:
            dTotOpeItem_EA008 = (dPUniProSer_E721 - dDescItem_EA002 - dDescGloItem_EA004 - dAntPreUniIt_EA006 - dAntGloPreUniIt_EA007) * dCantProSer_E711
        iAfecIVA_E731 = 1
        dPropIVA_E733 = 100
        dTasaIVA_E734 = 10
        for tax in self.tax_ids:
            tax_data = tax._get_sifen_data()
            iAfecIVA_E731 = tax_data.get('iAfecIVA_E731')
            dPropIVA_E733 = tax_data.get('dPropIVA_E733')
            dTasaIVA_E734 = tax_data.get('dTasaIVA_E734')
        # NT 13
        # E735 = dBasGravIVA = Base gravada del IVA por ítem
        #    Si E731 = 1 o 4 este campo es igual al resultado del cálculo:
        #        [100 * EA008 * E733] / [10000 + (E734 * E733)]
        #    Si E731 = 2 o 3 este campo es igual 0
        dBasGravIVA_E735 = 0.0
        if iAfecIVA_E731 in ( 1, 4):
            dTasaIVA_E734_f = float(dTasaIVA_E734 or 10.0)
            dPropIVA_E733_f = float(dPropIVA_E733 or 100.0)
            dBasGravIVA_E735 = ( 100.0 * dTotOpeItem_EA008 * dPropIVA_E733_f) / ( 10000.0 + ( dTasaIVA_E734_f * dPropIVA_E733_f))
        # NT 13
        # E737 = dBasExe = Base Exenta por ítem
        #    Si E731 = 4 este campo es igual al resultado del cálculo:
        #        [100 * EA008 * (100 – E733)] / [10000 + (E734 * E733)]
        #    Si E731 = 1 , 2 o 3 este campo es igual 0
        dBasExe_E737 = 0.0
        if iAfecIVA_E731 == 4:
            dTasaIVA_E734_f = float(dTasaIVA_E734 or 5.0)
            dPropIVA_E733_f = float(dPropIVA_E733 or 100.0)
            dBasExe_E737 = ( 100.0 * dTotOpeItem_EA008 * ( 100.0 - dPropIVA_E733_f)) / ( 10000.0 + ( dTasaIVA_E734_f * dPropIVA_E733_f))
        elif iAfecIVA_E731 == 3:
            dBasExe_E737 = dTotOpeItem_EA008
        # E736 = dLiqIVAItem = Liquidación del IVA por ítem
        # Corresponde al cálculo aritmético: E735 * (E734/100) Si E731 = 2 o 3 este campo es igual 0 
        dLiqIVAItem_E736 = 0.0
        if iAfecIVA_E731 in ( 1, 4):
            dTasaIVA_E734_f = float(dTasaIVA_E734 or 10.0)
            dLiqIVAItem_E736 = dBasGravIVA_E735 * ( dTasaIVA_E734_f / 100.0)
        #
        return {
            'dCantProSer_E711': dCantProSer_E711,
            'dPUniProSer_E721': dPUniProSer_E721,
            'dDescItem_EA002': dDescItem_EA002,
            'dDescGloItem_EA004': dDescGloItem_EA004,
            'dAntPreUniIt_EA006': dAntPreUniIt_EA006,
            'dTotOpeItem_EA008': dTotOpeItem_EA008,
            'iAfecIVA_E731': iAfecIVA_E731,
            'dPropIVA_E733': dPropIVA_E733,
            'dTasaIVA_E734': dTasaIVA_E734,
            'dBasGravIVA_E735': dBasGravIVA_E735,
            'dLiqIVAItem_E736': dLiqIVAItem_E736,
            'dBasExe_E737': dBasExe_E737,
        }
        