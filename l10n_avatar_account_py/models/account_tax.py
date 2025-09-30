# -*- coding: utf-8 -*-

from odoo import fields, models, api

class PyAccountTax(models.Model):

    _inherit = "account.tax"

    l10n_avatar_py_tax_assessment = fields.Selection([
        ('1','Gravado IVA'),
        ('2','Exonerado (Art. 83- Ley 125/91)'),
        ('3','Exento'),
        ('4','Gravado parcial (Grav-Exento)'),
    ], string="Afectación tributaria", default="1")

    l10n_avatar_py_base_tax = fields.Selection([
        ('100','100'),
        ('50','50'),
        ('30','30'),
        ('0','0'),
    ], default='100', string="Proporción gravada")
    
    # Retenciones
    l10n_avatar_py_withholding_payment_type = fields.Selection(
        selection=[('supplier', 'Pago a proveedores'), ('customer', 'Pago a clientes')],
        string="Tipo de pago de retención",
        help="Retención de impuestos para pagos a proveedores o clientes.")
    
    l10n_avatar_py_type_tax_use = fields.Selection(
        selection=[
            ('sale', 'Ventas'),
            ('purchase', 'Compras'),
            ('none', 'Otros'),
            ('supplier', 'Retención de pago a proveedores'),
            ('customer', 'Retención de pago del cliente')
        ],
        compute='_compute_l10n_avatar_py_type_tax_use', inverse='_inverse_l10n_avatar_py_type_tax_use',
        string="Argentina Tax Type"
    )

    l10n_avatar_py_tax_type = fields.Selection(
        string='WTH Tax',
        selection=[
            ('earnings', 'Earnings'),
            ('earnings_scale', 'Earnings Scale'),
            ('iibb_untaxed', 'IIBB Untaxed'),
            ('iibb_total', 'IIBB Total Amount'),
        ]
    )

    l10n_avatar_py_withholding_sequence_id = fields.Many2one(
        'ir.sequence', string='WTH Sequence', copy=False, check_company=True,
        help='Si no se proporciona ninguna secuencia, se le solicitará que ingrese el número de retención al registrar uno.'
    )

    l10n_avatar_py_code = fields.Char('Código interno')

    l10n_avatar_py_non_taxable_amount = fields.Float(
        string='Monto no imponible', digits='Account', 
        help="Hasta este importe base no se aplica el impuesto."
    )

    l10n_avatar_py_scale_id = fields.Many2one(
        comodel_name='l10n_avatar_py_earnings_scale', string="Scale",
    )

    l10n_avatar_py_minimum_threshold = fields.Float( string="Minimum Treshold",)

    @api.depends('type_tax_use', 'l10n_avatar_py_withholding_payment_type')
    def _compute_l10n_avatar_py_type_tax_use(self):
        for tax in self:
            if tax.country_code == 'PY':
                if tax.type_tax_use in ('sale', 'purchase'):
                    tax.l10n_avatar_py_type_tax_use = tax.type_tax_use
                elif tax.l10n_avatar_py_withholding_payment_type in ('supplier', 'customer'):
                    tax.l10n_avatar_py_type_tax_use = tax.l10n_avatar_py_withholding_payment_type
                else:
                    tax.l10n_avatar_py_type_tax_use = 'none'
            else:
                tax.l10n_avatar_py_type_tax_use = 'none'

    @api.onchange('l10n_avatar_py_type_tax_use')
    def _inverse_l10n_avatar_py_type_tax_use(self):
        for tax in self.filtered(lambda t: t.country_code == 'PY'):
            if tax.l10n_avatar_py_type_tax_use in ('sale', 'purchase'):
                tax.type_tax_use = tax.l10n_avatar_py_type_tax_use
                tax.l10n_avatar_py_tax_type = False
                #tax.l10n_ar_state_id = False
                tax.l10n_avatar_py_withholding_payment_type = False
            else:
                if tax.l10n_avatar_py_type_tax_use in ('supplier', 'customer'):
                    tax.l10n_avatar_py_withholding_payment_type = tax.l10n_avatar_py_type_tax_use
                else:
                    tax.l10n_avatar_py_withholding_payment_type = False
                    tax.l10n_avatar_py_tax_type = False
                tax.type_tax_use = 'none'

    def _get_sifen_data(self):
        # E731 = iAfecIVA = Forma de afectación tributaria del IVA
        #    1= Gravado IVA, 2= Exonerado (Art. 83- Ley 125/91)
        #    3= Exento, 4= Gravado parcial (Grav-Exento)
        iAfecIVA_E731 = int(self.l10n_avatar_py_tax_assessment)
		
        # E733 = dPropIVA = Proporción gravada de IVA. Corresponde al porcentaje (%) gravado Ejemplo:100, 50, 30, 0
        dPropIVA_E733 = int(self.l10n_avatar_py_base_tax)
		
        # E734 = dTasaIVA = Tasa del IVA. Corresponde al porcentaje (%) de la tasa expresado en números enteros
        dTasaIVA_E734 = 0
        if iAfecIVA_E731 in ( 1, 4):
            dTasaIVA_E734 = int(self.tax_group_id.l10n_avatar_py_tax_type)
        #
        return {
            'iAfecIVA_E731': iAfecIVA_E731,
            'dPropIVA_E733': dPropIVA_E733,
            'dTasaIVA_E734': dTasaIVA_E734,
		}
