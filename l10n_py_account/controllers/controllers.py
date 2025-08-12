# -*- coding: utf-8 -*-
# from odoo import http


# class L10nPyAccount(http.Controller):
#     @http.route('/l10n_py_account/l10n_py_account', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/l10n_py_account/l10n_py_account/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('l10n_py_account.listing', {
#             'root': '/l10n_py_account/l10n_py_account',
#             'objects': http.request.env['l10n_py_account.l10n_py_account'].search([]),
#         })

#     @http.route('/l10n_py_account/l10n_py_account/objects/<model("l10n_py_account.l10n_py_account"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('l10n_py_account.object', {
#             'object': obj
#         })

