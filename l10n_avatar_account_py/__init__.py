# -*- coding: utf-8 -*-

from . import controllers
from . import models
from . import demo
from . import wizards
from . import reports

def _pre_init_hook(env):
    #sql = "UPDATE ir_model_data SET noupdate=false WHERE model = '%s' AND modele = '%s'", 'l10n_latam_identification_type', 'l10n_latam'
    #env.cr.execute("UPDATE ir_model_data SET noupdate=false WHERE model = 'uom.uom' AND module = 'uom'")
    env.cr.execute( _get_update("false", "l10n_latam_identification_type", "l10n_latam"))
    env.cr.execute( _get_update("false", "uom.uom", "uom"))

def _post_init_hook(env):
    #env.cr.execute("UPDATE ir_model_data SET noupdate=true WHERE model = 'uom.uom' AND module = 'uom'")
    env.cr.execute( _get_update("true", "l10n_latam_identification_type", "l10n_latam"))
    env.cr.execute( _get_update("true", "uom.uom", "uom"))

def _get_update(value, model, module):
    sql = "UPDATE ir_model_data SET noupdate=" + str(value)
    sql += " WHERE model = '" + model + "' AND module = '" + module + "'"
    return sql
    