# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError, RedirectWarning

# Para que no de error el IDE
from odoo.addons.base.models.res_partner import Partner

import logging

_logger = logging.getLogger(__name__)

class AccountJournal(models.Model):

    _inherit = "account.journal"

    l10n_py_dnit_pos_system = fields.Selection(
        selection='_get_l10n_py_dnit_pos_types_selection', string='DNIT POS System',
        compute='_compute_l10n_py_dnit_pos_system', store=True, readonly=False,
        help="Paraguay: Specify which type of system will be used to create the electronic invoice. This will depend on the type of invoice to be created.",
    )

    l10n_py_dnit_pos_number = fields.Integer(
        'Punto de expedición', help='Este es el número de punto de expedición asignado por la DNIT para generar facturas')

    l10n_py_is_pos = fields.Boolean(
        compute="_compute_l10n_py_is_pos", store=True, readonly=False,
        string="¿Con conecxión a la DNIT?",
        help="Especificar si este Diario será utilizado para enviar facturas electrónicas a la DNIT",
    )

    company_partner = fields.Many2one('res.partner', related='company_id.partner_id')

    l10n_py_dnit_pos_partner_id = fields.Many2one(
        'res.partner', 'DNIT POS Address', help='Esta es la dirección utilizada para las facturas',
        domain="['|', ('id', '=', company_partner), '&', ('id', 'child_of', company_partner), ('type', '!=', 'contact')]"
    )

    @api.depends('country_code', 'type', 'l10n_latam_use_documents')
    def _compute_l10n_py_is_pos(self):
        for journal in self:
            journal.l10n_py_is_pos = journal.country_code == 'PY' and journal.type == 'sale' and journal.l10n_latam_use_documents

    def _get_l10n_py_dnit_pos_types_selection(self):
        """ Return the list of values of the selection field. """
        return [
            ('II_IM', _('Factura preimpresa')),
            ('RLI_RLM', _('Factura en línea')),
            ('AUII_IM', _('Autofactura preimpresa')),
            ('AURLI_RLM', _('Autofactura en línea')),
            ('BFERCEL', _('Bono Fiscal Electrónico - Factura en Línea')),
            ('FEERCELP', _('Comprobante de exportación - Billing Plus')),
            ('FEERCEL', _('Comprobante de Exportación - Factura en Línea')),
            ('CPERCEL', _('Codificación de productos - Cupón en línea')),
        ]

    @api.depends('l10n_py_is_pos')
    def _compute_l10n_py_dnit_pos_system(self):
        for journal in self:
            journal.l10n_py_dnit_pos_system = journal.l10n_py_is_pos and journal.l10n_py_dnit_pos_system

    ###
    ### Constraints
    ###
    @api.constrains('l10n_py_dnit_pos_system')
    def _check_dnit_pos_system(self):
        journals = self.filtered(
            lambda j: j.l10n_py_is_pos and j.type == 'purchase' and
            j.l10n_py_dnit_pos_system not in ['II_IM', 'AUII_IM', 'RLI_RLM', 'AURLI_RLM', 'RAW_MAW'])
        if journals:
            raise ValidationError("\n".join(
                _("The pos system %(system)s can not be used on a purchase journal (id %(id)s)", system=x.l10n_py_dnit_pos_system, id=x.id)
                for x in journals
            ))

    @api.constrains('l10n_py_dnit_pos_number')
    def _check_dnit_pos_number(self):
        if self.filtered(lambda j: j.l10n_py_is_pos and j.l10n_py_dnit_pos_number == 0):
            raise ValidationError(_('Please define an DNIT POS number'))

        if self.filtered(lambda j: j.l10n_py_is_pos and j.l10n_py_dnit_pos_number > 999):
            raise ValidationError(_('Please define a valid DNIT POS number (3 digits max)'))

    ###
    ### 
    ###
    @api.onchange('l10n_py_dnit_pos_number', 'type')
    def _onchange_set_short_name(self):
        """ Will define the DNIT POS Address field domain taking into account the company configured in the journal
        The short code of the journal only admit 5 characters, so depending on the size of the pos_number (also max 5)
        we add or not a prefix to identify sales journal.
        """
        if self.type == 'sale' and self.l10n_py_dnit_pos_number and 0 == 1:  ## Forzamos a que no se ejecute nunca
            self.code = "%05i" % self.l10n_py_dnit_pos_number

    ###
    ### 
    ###
    def _get_journal_letter(self, counterpart_partner:Partner):
        """ Regarding the DNIT responsibility of the company and the type of journal (sale/purchase), get the allowed
        letters. Optionally, receive the counterpart partner (customer/supplier) and get the allowed letters to work
        with him. This method is used to populate document types on journals and also to filter document types on
        specific invoices to/from customer/supplier
        """
        self.ensure_one()
        # 1:Contribuyente, 4:Exento, 5:Consumidor Final, 7: NN, 8: Prov ext, 9:Cliente Ext
        letters_data = {
            'issued': {
                '1': ['A', 'B', 'E', 'M','C'],
                '4': ['C'],
                '5': ['C'],
                '6': ['C', 'E'],
                '7': ['B', 'C', 'I'],
                '8': ['B', 'C', 'I'],
                '9': ['I'],
                '10': [],
                '13': ['C', 'E'],
                '15': [],
                '16': [],
            },
            'received': {
                '1': ['A', 'B', 'C', 'E', 'M', 'I'],
                '4': ['B', 'C', 'I'],
                '5': ['A','B', 'C', 'I'],
                '6': ['A', 'B', 'C', 'M', 'I'],
                '7': ['B', 'C', 'I'],
                '8': ['E', 'B', 'C'],
                '9': ['E', 'B', 'C'],
                '10': ['E', 'B', 'C'],
                '13': ['A', 'B', 'C', 'M', 'I'],
                '15': ['B', 'C', 'I'],
                '16': ['A', 'C', 'M'],
            },
        }
        if not self.company_id.l10n_py_dnit_responsibility_type_id:
            action = self.env.ref('base.action_res_company_form')
            msg = _('Can not create chart of account until you configure your company DNIT Responsibility and VAT.')
            raise RedirectWarning(msg, action.id, _('Go to Companies'))

        letters = letters_data['issued' if self.l10n_py_is_pos else 'received'][
            self.company_id.l10n_py_dnit_responsibility_type_id.code]
        if counterpart_partner and counterpart_partner != None:
            counterpart_letters = letters_data['issued' if not self.l10n_py_is_pos else 'received'].get(
                counterpart_partner.l10n_py_dnit_responsibility_type_id.code, [])
            letters = list(set(letters) & set(counterpart_letters))
        return letters

    def _get_journal_codes_domain(self):
        self.ensure_one()
        return self._get_codes_per_journal_type(self.l10n_py_dnit_pos_system)

    @api.model
    def _get_codes_per_journal_type(self, dnit_pos_system):
        usual_codes = ['1', '2', '3', '6', '7', '8', '11', '12', '13']
        mipyme_codes = ['201', '202', '203', '206', '207', '208', '211', '212', '213']
        invoice_m_code = ['51', '52', '53']
        receipt_m_code = ['54']
        receipt_codes = ['4', '9', '15']
        expo_codes = ['19', '20', '21']
        zeta_codes = ['80', '83']
        codes_issuer_is_supplier = [
            '23', '24', '25', '26', '27', '28', '33', '43', '45', '46', '48', '58', '60', '61', '150', '151', '157',
            '158', '161', '162', '164', '166', '167', '171', '172', '180', '182', '186', '188', '332']
        auto_factura = ['2000']
        codes = []
        #if (self.type == 'purchase' and dnit_pos_system in ['AUII_IM', 'AURLI_RLM']):
        #    codes = auto_factura
        if (self.type == 'sale' and not self.l10n_py_is_pos) or (self.type == 'purchase' and dnit_pos_system in ['II_IM', 'RLI_RLM']):
            codes = codes_issuer_is_supplier
        elif self.type == 'purchase' and dnit_pos_system == 'RAW_MAW':
            # electronic invoices (wsfev1) (intersection between available docs on ws and codes_issuer_is_supplier)
            codes = ['60', '61']
        elif self.type == 'purchase':
            return [('code', 'not in', codes_issuer_is_supplier)]
        elif dnit_pos_system == 'II_IM':
            # pre-printed invoice
            codes = usual_codes + receipt_codes + expo_codes + invoice_m_code + receipt_m_code
        elif dnit_pos_system == 'RAW_MAW':
            # electronic/online invoice
            codes = usual_codes + receipt_codes + invoice_m_code + receipt_m_code + mipyme_codes
        elif dnit_pos_system == 'RLI_RLM':
            codes = usual_codes + receipt_codes + invoice_m_code + receipt_m_code + mipyme_codes + zeta_codes
        elif dnit_pos_system in ['CPERCEL', 'CPEWS']:
            # invoice with detail
            codes = usual_codes + invoice_m_code
        elif dnit_pos_system in ['BFERCEL', 'BFEWS']:
            # Bonds invoice
            codes = usual_codes + mipyme_codes
        elif dnit_pos_system in ['FEERCEL', 'FEEWS', 'FEERCELP']:
            codes = expo_codes
        return [('code', 'in', codes)]


    ###
    ###
    ###
    def write(self, vals):
        protected_fields = ('type', 'l10n_py_dnit_pos_system', 'l10n_py_dnit_pos_number', 'l10n_latam_use_documents')
        fields_to_check = [field for field in protected_fields if field in vals]

        if fields_to_check:
            self._cr.execute("SELECT DISTINCT(journal_id) FROM account_move WHERE posted_before = True")
            res = self._cr.fetchall()
            journal_with_entry_ids = [journal_id for journal_id, in res]

            for journal in self:
                if (
                    journal.company_id.account_fiscal_country_id.code != "PY"
                    or journal.type not in ['sale', 'purchase']
                    or journal.id not in journal_with_entry_ids
                ):
                    continue

                for field in fields_to_check:
                    # Wouldn't work if there was a relational field, as we would compare an id with a recordset.
                    if vals[field] != journal[field]:
                        raise UserError(_("You can not change %s journal's configuration if it already has validated invoices", journal.name))

        return super().write(vals)

    l10n_py_dnit_timbrado = fields.Char(string="Numero de Timbrado (PROD)")
    l10n_py_dnit_timbrado_test = fields.Char(string="Numero de Timbrado (TEST)")
    l10n_py_dnit_timbrado_start_date = fields.Date(string="Fecha de inicio dell timbrado (PROD)")
    l10n_py_dnit_timbrado_start_date_test = fields.Date(string="Fecha de inicio dell timbrado (TEST)")
    l10n_py_dnit_timbrado_end_date = fields.Date(string="Fecha de fin dell timbrado (PROD)")
    l10n_py_dnit_timbrado_end_date_test = fields.Date(string="Fecha de fin dell timbrado (TEST)")
    