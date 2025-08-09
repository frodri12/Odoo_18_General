# -*- coding: utf-8 -*-

from . import controllers
from . import models

def _pre_change_values(env):
    env.cr.execute("UPDATE ir_model_data SET noupdate=false WHERE model = 'uom.uom' AND module = 'uom'")

def _post_change_values(env):
    env.cr.execute("UPDATE ir_model_data SET noupdate=true WHERE model = 'uom.uom' AND module = 'uom'")
