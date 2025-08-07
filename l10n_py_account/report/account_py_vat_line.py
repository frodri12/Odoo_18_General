#
from odoo import api, fields, models, tools
from odoo.tools import SQL

class AccountPyVatLine(models.Model):

    _name = "account.py.vat.line"
    _description = "account.py.vat.line"
    _rec_name = 'move_name'
    _auto = False
    _order = 'invoice_date asc, move_name asc, id asc'

    move_name = fields.Char(readonly=True)
    date = fields.Date(readonly=True)
    invoice_date = fields.Date(readonly=True)
    move_id = fields.Many2one( 'account.move', string="Entry", auto_join=True, index='btree_not_null')
    company_id = fields.Many2one('res.company', 'Company', readonly=True, auto_join=True)
    company_currency_id = fields.Many2one(related='company_id.currency_id', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Partner', readonly=True, auto_join=True)
    journal_id = fields.Many2one('account.journal', 'Journal', readonly=True, auto_join=True)

    state = fields.Selection([('draft','Unposted'), ('posted','Posted')], 'Status', readonly=True)
    move_type = fields.Selection([('entry','Journal Entry'),
                                  ('out_invoice','Customer Invoice'),
                                  ('out_refund','Customer Credit Note'),
                                  ('in_invoice','Vendor Bill'),
                                  ('in_refund','Vendor Credit Note'),
                                  ('out_receipt','Sales Receipt'),
                                  ('in_receipt','Purchase Receipt')], readonly=True)

    partner_name = fields.Char(readonly=True)
    partner_vat = fields.Char('RUC/Identificacion',readonly=True)
    partner_timbrado = fields.Char(readonly=True)
    base_10 = fields.Monetary(readonly=True, currency_field='company_currency_id', string="Grav. 10%")
    base_5 = fields.Monetary(readonly=True, currency_field='company_currency_id', string="Grav. 5%")
    not_taxed = fields.Monetary(readonly=True, currency_field='company_currency_id', string="Exento")
    vat_10 = fields.Monetary(readonly=True, currency_field='company_currency_id', string="VAT 10%")
    vat_5 = fields.Monetary(readonly=True, currency_field='company_currency_id', string="VAT 5%")
    base_tax10 = fields.Monetary(readonly=True, currency_field='company_currency_id', string="G 10%")
    base_tax5 = fields.Monetary(readonly=True, currency_field='company_currency_id', string="G 5%")
    base_exe = fields.Monetary(readonly=True, currency_field='company_currency_id', string="Base Exento")

    tipo_identificacion = fields.Char("TIPO IDENTIFICACION") 
    l10n_latam_identification_type_id = fields.Many2one('l10n_latam.identification.type', 'TIPO DE IDENTIFICACION', readonly=True, auto_join=True)

    def open_journal_entry(self):
        self.ensure_one()
        return self.move_id.get_formview_action()

    def init(self):
        cr = self._cr
        tools.drop_view_if_exists( cr, self._table)
        query = self._py_vat_line_build_query()
        sql = SQL("""CREATE OR REPLACE VIEW account_py_vat_line as (%s)""", query)
        cr.execute(sql)

    @property
    def _table_query(self) -> SQL:
        return self._py_vat_line_build_query()

    @api.model
    def _py_vat_line_build_query( self, table_references=None, search_condition=None, column_group_key='', tax_types=('sale','purchase')) -> SQL:
        if table_references is None:
            table_references = SQL('account_move_line')
        search_condition = SQL('AND (%s)', search_condition) if search_condition else SQL()

        query = SQL(
            """
                SELECT
                     %(column_group_key)s AS column_group_key,
                     account_move.id,
                     account_move.id AS move_id,
                     account_move.name AS move_name,
                     account_move.date,
                     account_move.invoice_date,
                     account_move.state,
                     account_move.partner_id,
                     account_move.journal_id,
                     account_move.company_id,
                     account_move.move_type,
                     rp.name AS partner_name,
                     rp.vat AS partner_vat,
                     rp.l10n_latam_identification_type_id,
                     account_move.l10n_py_dnit_auth_code AS partner_timbrado,
                     SUM(CASE WHEN btg.l10n_py_vat_dnit_code = '5' THEN account_move_line.balance ELSE 0 END) base_10,
                     SUM(CASE WHEN btg.l10n_py_vat_dnit_code = '4' THEN account_move_line.balance ELSE 0 END) base_5,
                     SUM(CASE WHEN btg.l10n_py_vat_dnit_code = '3' THEN account_move_line.balance ELSE 0 END) not_taxed,
                     SUM(CASE WHEN ntg.l10n_py_vat_dnit_code = '5' THEN account_move_line.balance ELSE 0 END) vat_10,
                     SUM(CASE WHEN ntg.l10n_py_vat_dnit_code = '5' THEN account_move_line.balance ELSE 0 END) vat_5,
                     SUM(CASE WHEN account_move_line.balance < 0 THEN (-1) * account_move_line.l10n_py_base_grav_tax10 ELSE account_move_line.l10n_py_base_grav_tax10 END) base_tax10,
                     SUM(CASE WHEN account_move_line.balance < 0 THEN (-1) * account_move_line.l10n_py_base_grav_tax5 ELSE account_move_line.l10n_py_base_grav_tax5 END) base_tax5,
                     SUM(CASE WHEN account_move_line.balance < 0 THEN (-1) * account_move_line.l10n_py_base_grav_exe ELSE account_move_line.l10n_py_base_grav_exe END) base_exe
                  FROM
                      %(table_references)s
                      JOIN account_move ON account_move_line.move_id = account_move.id
                      LEFT JOIN account_tax AS nt ON account_move_line.tax_line_id = nt.id
                      LEFT JOIN account_move_line_account_tax_rel AS amltr ON account_move_line.id = amltr.account_move_line_id
                      LEFT JOIN account_tax AS bt ON amltr.account_tax_id = bt.id
                      LEFT JOIN account_tax_group AS btg ON btg.id = bt.tax_group_id
                      LEFT JOIN account_tax_group AS ntg ON ntg.id = nt.tax_group_id
                      LEFT JOIN res_partner AS rp ON rp.id = account_move.commercial_partner_id
                  WHERE
                      (account_move_line.tax_line_id is not NULL OR btg.l10n_py_vat_dnit_code is not NULL)
                      AND (nt.type_tax_use in %(tax_types)s OR bt.type_tax_use in %(tax_types)s)
                      %(search_condition)s
                  GROUP BY 
                      account_move.id, rp.id, COALESCE(nt.type_tax_use, bt.type_tax_use)
                  ORDER BY
                      account_move.invoice_date, account_move.name
            """,
            column_group_key=column_group_key,
            table_references=table_references,
            tax_types=tax_types,
            search_condition=search_condition,
        )
        return query

