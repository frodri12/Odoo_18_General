# -*- coding: utf-8 -*-
# from odoo import http


# class L10nAvatarAccountPy(http.Controller):
#     @http.route('/l10n_avatar_account_py/l10n_avatar_account_py', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/l10n_avatar_account_py/l10n_avatar_account_py/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('l10n_avatar_account_py.listing', {
#             'root': '/l10n_avatar_account_py/l10n_avatar_account_py',
#             'objects': http.request.env['l10n_avatar_account_py.l10n_avatar_account_py'].search([]),
#         })

#     @http.route('/l10n_avatar_account_py/l10n_avatar_account_py/objects/<model("l10n_avatar_account_py.l10n_avatar_account_py"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('l10n_avatar_account_py.object', {
#             'object': obj
#         })

