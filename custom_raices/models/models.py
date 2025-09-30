# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class custom_raices(models.Model):
#     _name = 'custom_raices.custom_raices'
#     _description = 'custom_raices.custom_raices'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

