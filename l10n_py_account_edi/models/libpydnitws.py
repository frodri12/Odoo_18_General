#

from odoo.exceptions import ValidationError
from datetime import datetime

import logging
_logger = logging.getLogger(__name__)


from . import libpydate
import json
import re

# response_data = libdnitws.get_response_dnit( response_data)
# self.l10n_py_dnit_ws_response_json = json.dumps(response_data.json(), indent=4)
# self.l10n_py_dnit_ws_response_fecproc = datetime.now()
# self.l10n_py_dnit_ws_response_estres = 'E'
# self.l10n_py_dnit_ws_response_msgres = response.get("message")
# self.l10n_py_dnit_ws_response_cdc = dId
# self.l10n_py_dnit_ws_response_fecproc = datetime.strptime(dFecProc, "%Y-%m-%dT%H:%M:%S")
# self.l10n_py_dnit_ws_response_estres = dEstRes[:1]
# self.l10n_py_dnit_ws_response_codres = dCodRes
# self.l10n_py_dnit_ws_response_msgres = dMsgRes


def process_response_dnit( response_data):
    """
    Process the response from the DNIT
    """
    return_value = {}
    #response = response_data.json()
    response = json.loads(response_data) 

    if int(response['code']) != 0:
        _logger.error(str(response))
        return_value.update({'dEstRes': 'E'})
        return_value.update({'dCodRes': str(response['code'])})
        return_value.update({'dMsgRes': response.get("message")})
        payload = response.get("payload")
        if payload and payload != None:
            if payload.get('errno') and payload.get('errno') != None:
                return_value.update({'dCodRes': str(payload['errno'])})
            if payload.get('errstr') and payload.get('errstr') != None:
                return_value.update({'dMsgRes': str(payload['errstr'])})
        return return_value

    _logger.info(str(response))
    rProtDe = _get_rProtDe( response)
    if rProtDe == None:
        return return_value
    return_value.update({'dId': rProtDe.get("ns2:Id")})
    #return_value.update({'dFecProc': libpydate.from_date2utc(rProtDe.get("ns2:dFecProc"))})
    #return_value.update({'dFecProc': datetime.strptime((rProtDe.get("ns2:dFecProc")[0:10] + " " + rProtDe.get("ns2:dFecProc")[11:19]), "%Y-%m-%d %H:%M:%S")})
    return_value.update({'dFecProc': rProtDe.get("ns2:dFecProc")[0:19]})
    if rProtDe.get("ns2:dEstRes") == None:
        return_value.update({'dEstRes': "E"})
    else:
        return_value.update({'dEstRes': rProtDe.get("ns2:dEstRes")[:1]})
    return_value.update({'dEstResDet': rProtDe.get("ns2:dEstRes")})
    return_value.update({'dProtAut': rProtDe.get("ns2:dProtAut")})

    gResProc = rProtDe.get("ns2:gResProc")
    if not gResProc or gResProc == None:
        return return_value

    if str(type(gResProc)) == "<class 'dict'>":
        return_value.update({'dCodRes': gResProc.get("ns2:dCodRes")})
        return_value.update({'dMsgRes': gResProc.get("ns2:dMsgRes")})
    elif str(type(gResProc)) == "<class 'list'>":
        for rec in gResProc:
            return_value.update({'dCodRes': rec.get("ns2:dCodRes")})
            return_value.update({'dMsgRes': rec.get("ns2:dMsgRes")})
    return return_value

def _get_rProtDe( response):
    payload = response.get("payload")
    if not payload or payload == None:
        return None
    rRetEnviDe = payload.get("ns2:rRetEnviDe")
    if not rRetEnviDe or rRetEnviDe == None:
        return None
    return rRetEnviDe.get("ns2:rProtDe")
