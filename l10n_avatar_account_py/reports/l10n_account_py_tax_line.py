# -*- coding: utf-8 -*-

from odoo import fields, models, api, tools, _
from odoo.tools import SQL

import logging
_logger = logging.getLogger(__name__)

class PyAccountTaxLine(models.Model):

    _name = "l10n_account_py_tax_line"
    _description = "TAX line for Analysis in Paraguay Localization"
    _rec_name = 'move_name'
    _auto = False
    _check_company_auto = True
    _order = 'invoice_date asc, move_name asc, id asc'

    move_id = fields.Many2one('account.move', string='Entry', auto_join=True, index='btree_not_null', check_company=True)
    move_name = fields.Char(readonly=True)
    document_type_id = fields.Many2one('l10n_latam.document.type', 'Document Type', readonly=True)
    journal_id = fields.Many2one('account.journal', 'Journal', readonly=True, auto_join=True)
    partner_id = fields.Many2one('res.partner', 'Partner', readonly=True, auto_join=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True, auto_join=True)
    company_currency_id = fields.Many2one(related='company_id.currency_id', readonly=True)
    l10n_latam_identification_type_id = fields.Many2one('l10n_latam.identification.type', 'Tipo Identificación', readonly=True, auto_join=True)

    date = fields.Date(string="Fecha de Emisión", readonly=True)
    invoice_date = fields.Date(readonly=True)

    move_type = fields.Selection(selection=[
            ('entry', 'Journal Entry'),
            ('out_invoice', 'Customer Invoice'),
            ('out_refund', 'Customer Credit Note'),
            ('in_invoice', 'Vendor Bill'),
            ('in_refund', 'Vendor Credit Note'),
            ('out_receipt', 'Sales Receipt'),
            ('in_receipt', 'Purchase Receipt'),
        ], readonly=True)
    partner_name = fields.Char(string="Nombre/Razón Social", readonly=True)
    state = fields.Selection([('draft', 'Unposted'), ('posted', 'Posted')], 'Status', readonly=True)
    journal_type = fields.Selection([('sale', 'Sale'), ('purchase', 'Purchase')], 'Journal Type', readonly=True)
    l10n_avatar_py_poe_system = fields.Char(readonly=True)
    latam_identification_name = fields.Char(readonly=True)
    partner_vat = fields.Char(string="RUC/Identificación", readonly=True)
    l10n_latam_document_number = fields.Char(
        related='move_id.l10n_latam_document_number',
        string='Número de Comprobante/documento', readonly=False)
    document_type = fields.Char(related='document_type_id.name',string='Tipo Comprobante', readonly=False)
    timbrado = fields.Char(related='move_id.l10n_avatar_py_authorization_code',string='Timbrado', readonly=False)

    amount_total = fields.Monetary(readonly=True, string='Importe Total del comprobante', currency_field='company_currency_id')
    amount_base_exempt = fields.Monetary(readonly=True, string='Importe Exenta', currency_field='company_currency_id')
    amount_base_5 = fields.Monetary(readonly=True, string='Total gravadas 5%', currency_field='company_currency_id')
    amount_tax_base_5 = fields.Monetary(readonly=True, string='IVA 5%', currency_field='company_currency_id')
    amount_base_10 = fields.Monetary(readonly=True, string='Total gravadas 10%', currency_field='company_currency_id')
    amount_tax_base_10 = fields.Monetary(readonly=True, string='IVA 10%', currency_field='company_currency_id')
    amount_total_tax = fields.Monetary(readonly=True, string='Total importe sin IVA', currency_field='company_currency_id')

    def open_journal_entry(self):
        self.ensure_one()
        return self.move_id.get_formview_action()

    def init(self):
        cr = self._cr
        tools.drop_view_if_exists(cr, self._table)
        query = self._py_tax_line_build_query()
        sql = SQL("""CREATE or REPLACE VIEW l10n_account_py_tax_line as (%s)""", query)
        cr.execute(sql)

    @property
    def _table_query(self):
        if self.env.context.get('tax_types'):
            if self.env.context.get('tax_types') == 'purchase':
                _logger.error( self.env.context)
                return self._py_tax_line_build_query(tax_types=('purchase','',''))
            elif self.env.context.get('tax_types') == 'sale':
                _logger.error( self.env.context)
                return self._py_tax_line_build_query(tax_types=('ventas','sale',''))
            
        return self._py_tax_line_build_query()

    @api.model
    def _py_tax_line_build_query(
        self, table_references=None, search_condition=None, 
        column_group_key='', tax_types=('sale', 'purchase')) -> SQL:

        inv = 1
        af = 1
        if len(tax_types) == 3 and tax_types[0] == 'ventas':
            inv = -1
            #_logger.error( 'Pasamos por aca = %s' % str(inv))

        if table_references is None:
            table_references = SQL('account_move_line')
        search_condition = SQL('AND (%s)', search_condition) if search_condition else SQL()

        query = SQL(
            """
    SELECT %(column_group_key)s AS column_group_key,
           account_move.id,
           account_move.id as move_id,
           account_move.name AS move_name,
           account_move.l10n_latam_document_type_id as document_type_id,
           account_move.journal_id,
           account_move.partner_id,
           account_move.company_id,
           account_move.date,
           account_move.invoice_date,
           account_move.move_type,
           rp.name AS partner_name,
           rp.vat AS partner_vat,
           account_move.state,
           aj.type as journal_type,
           aj.l10n_avatar_py_poe_system,
           rp.l10n_latam_identification_type_id, 
           lit.name as latam_identification_name,
           --
           accline.balance,
           (CASE WHEN accline.amount_total != 0.0 
                THEN %(inv)s ELSE 1 END) * accline.amount_total as amount_total,
           (CASE WHEN accline.l10n_avatar_py_amount_currency_base_exempt != 0.0 
                THEN %(inv)s ELSE 1 END) * accline.l10n_avatar_py_amount_currency_base_exempt as amount_base_exempt,
           (CASE WHEN accline.l10n_avatar_py_amount_currency_base_5 != 0.0 
                THEN %(inv)s ELSE 1 END) * accline.l10n_avatar_py_amount_currency_base_5 as amount_base_5,
           (CASE WHEN accline.l10n_avatar_py_tax_currency_base_5 != 0.0 
                THEN %(inv)s ELSE 1 END) * accline.l10n_avatar_py_tax_currency_base_5 as amount_tax_base_5,
           (CASE WHEN accline.l10n_avatar_py_amount_currency_base_10 != 0.0 
                THEN %(inv)s ELSE 1 END) * accline.l10n_avatar_py_amount_currency_base_10 as amount_base_10,
           (CASE WHEN accline.l10n_avatar_py_tax_currency_base_10 != 0.0 
                THEN %(inv)s ELSE 1 END) * accline.l10n_avatar_py_tax_currency_base_10 as amount_tax_base_10,
           (CASE WHEN accline.amount_total_tax != 0.0 
                THEN %(inv)s ELSE 1 END) * accline.amount_total_tax as amount_total_tax

      FROM (
            SELECT move_id, SUM(balance) as balance,
                   SUM( CASE WHEN balance < 0.0 THEN -1 ELSE 1 END * (l10n_avatar_py_amount_currency_base_exempt + 
                        l10n_avatar_py_amount_currency_base_5 + 
                        l10n_avatar_py_amount_currency_base_10)) as amount_total,
                   SUM( CASE WHEN balance < 0.0 THEN -1 ELSE 1 END * l10n_avatar_py_amount_currency_base_exempt) as l10n_avatar_py_amount_currency_base_exempt,
                   SUM( CASE WHEN balance < 0.0 THEN -1 ELSE 1 END * l10n_avatar_py_amount_currency_base_5) as l10n_avatar_py_amount_currency_base_5,
                   SUM( CASE WHEN balance < 0.0 THEN -1 ELSE 1 END * l10n_avatar_py_tax_currency_base_5) as l10n_avatar_py_tax_currency_base_5,
                   SUM( CASE WHEN balance < 0.0 THEN -1 ELSE 1 END * l10n_avatar_py_amount_currency_base_10) as l10n_avatar_py_amount_currency_base_10,
                   SUM( CASE WHEN balance < 0.0 THEN -1 ELSE 1 END * l10n_avatar_py_tax_currency_base_10) as l10n_avatar_py_tax_currency_base_10,
                   SUM( CASE WHEN balance < 0.0 THEN -1 ELSE 1 END * (account_move_line.l10n_avatar_py_tax_currency_base_5 +
                        account_move_line.l10n_avatar_py_tax_currency_base_10 )) as amount_total_tax
              FROM %(table_references)s
             WHERE display_type NOT IN ( 'tax', 'payment_term')
            GROUP BY move_id
           ) as accline
      JOIN account_move ON accline.move_id = account_move.id
      LEFT JOIN res_partner AS rp ON rp.id = account_move.commercial_partner_id
      LEFT JOIN l10n_latam_identification_type AS lit ON rp.l10n_latam_identification_type_id = lit.id AND lit.l10n_avatar_py_code IS NOT NULL
      LEFT JOIN account_journal as aj ON aj.id = account_move.journal_id
     WHERE account_move.move_type NOT IN ('entry')
       AND aj.type IN %(tax_types)s
           %(search_condition)s
    ORDER BY account_move.invoice_date, account_move.name
            """,
            column_group_key=column_group_key,
            table_references=table_references,
            tax_types=tax_types,
            search_condition=search_condition,
            af=af,
            inv=inv
        )
        return query