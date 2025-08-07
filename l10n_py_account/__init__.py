# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api

from . import models
from . import demo
from . import report

def install_languages(env):
    """ Post init function """
    #env = api.Environment(cr, SUPERUSER_ID, {})

    # Install desired language if not installed
    es_PY_language = env['res.lang'].sudo().search([('code', '=', 'es_PY')], limit=1)
    if not es_PY_language:
        es_PY_language = env['res.lang'].with_context(active_test=False).sudo().search([('code', '=', 'es_PY')], limit=1)
        env['base.language.install'].create({'lang_ids': [(6, 0, es_PY_language.ids)]}).lang_install()

def _set_change_values(env):
    install_languages(env)
    env.cr.execute("UPDATE ir_model_data SET noupdate=false WHERE model = 'res.users' AND name = 'user_admin'")
    env.cr.execute("UPDATE ir_model_data SET noupdate=false WHERE model = 'res.partner' AND name = 'partner_admin'")

    