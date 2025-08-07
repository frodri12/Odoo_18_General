# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
import logging

_logger = logging.getLogger(__name__)

class l10nPyAccountMoveLine(models.Model):

    _inherit = 'account.move.line'

    def _get_l10n_py_dnit_ws_item(self):
        productId = self.product_id
        uomId = productId.uom_id
        item = {}
        item.update({"codigo": productId.default_code if productId.default_code else productId.id}) #E701
        item.update({"descripcion": productId.name}) #E708
        if uomId.l10n_py_dnit_code:
            item.update({"unidadMedida": uomId.l10n_py_dnit_code}) #E709
        item.update({"cantidad": self.quantity}) #E711
        # E8 E704-E707 - Pendiente de implementar
        item.update({"pais": "PRY"}) #E712
        item.update({"observacion": productId.name}) #E714
        # E8 E715-E719 - Pendiente de implementar
        item.update({"precioUnitario": self.price_unit}) #E721
        if self.currency_id.name != 'PYG':
            item.update({"cambio": 1 / self.currency_rate}) #E725
        # E8.1.1 EA001-EA007 - Pendiente de implementar
        ivaTipo = 1
        ivaBase = self.tax_ids.l10n_py_tax_base
        ivaAmount = self.tax_ids.amount
        if ivaAmount == 0:
            ivaTipo = 3
        elif ivaBase < 100 and ivaBase > 0:
            ivaAmount = self.tax_ids.amount * 100 / ivaBase
            ivaTipo = 4
        item.update({"ivaTipo": ivaTipo}) #E731
        item.update({"ivaBase": 0 if ivaTipo == 3 else ivaBase}) #E733
        item.update({"iva": ivaAmount}) #E734
        # E8.4 E750-E760 - Pendiente de implementar
        # E8.5 E770-E789 - Pendiente de implementar
        return item