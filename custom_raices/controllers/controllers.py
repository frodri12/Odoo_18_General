# -*- coding: utf-8 -*-
# from odoo import http


# class CustomRaices(http.Controller):
#     @http.route('/custom_raices/custom_raices', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/custom_raices/custom_raices/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('custom_raices.listing', {
#             'root': '/custom_raices/custom_raices',
#             'objects': http.request.env['custom_raices.custom_raices'].search([]),
#         })

#     @http.route('/custom_raices/custom_raices/objects/<model("custom_raices.custom_raices"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('custom_raices.object', {
#             'object': obj
#         })

