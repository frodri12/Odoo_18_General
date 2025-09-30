# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PyEarningsScale(models.Model):

    _name = 'l10n_avatar_py_earnings_scale'
    _description = 'l10n_avatar_py_earnings_scale'

    name = fields.Char(required=True, translate=True)
    line_ids = fields.One2many('l10n_avatar_py_earnings_scale_line', 'scale_id')

class PyEarningsScaleLine(models.Model):

    _name = 'l10n_avatar_py_earnings_scale_line'
    _description = 'l10n_avatar_py_earnings_scale_line'
    _order = 'to_amount'

    scale_id = fields.Many2one(
        'l10n_avatar_py_earnings_scale', required=True, ondelete='cascade',
    )
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.ref('base.PYG'), store=False
    )
    from_amount = fields.Monetary(
        string='From $', currency_field='currency_id', compute="_compute_from_amount"
    )
    to_amount = fields.Monetary( string='To $', currency_field='currency_id',)
    fixed_amount = fields.Monetary( string='$', currency_field='currency_id',)
    percentage = fields.Monetary( string='Add %', currency_field='currency_id',)
    excess_amount = fields.Monetary( string='S/ Exceeding $', currency_field='currency_id',)

    @api.depends('to_amount', 'scale_id.line_ids')
    def _compute_from_amount(self):
        for line in self:
            line.from_amount = line.scale_id.line_ids.sorted(reverse=True).filtered(lambda l: l.to_amount < line.to_amount)[:1].to_amount
