# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api, _
from odoo.exceptions import UserError

import logging
from datetime import datetime
import json
import os.path
from os import path
import requests

from . import libpyedi
from . import libpydnitws
import urllib.parse

_logger = logging.getLogger(__name__)

_params = {}
_data = {}

class AccountMove(models.Model):

    _inherit = "account.move"

    l10n_py_dnit_ws_response_cdc = fields.Char(string="CDC", readonly=True, tracking=True, copy=False)
    l10n_py_dnit_ws_response_fecproc = fields.Char(string="Fecha de procesado", readonly=True, tracking=True, copy=False)
    l10n_py_dnit_ws_response_digval = fields.Char(string="Digito de verificacion", readonly=True, tracking=True, copy=False)
    l10n_py_dnit_ws_response_estres = fields.Selection(selection=[
            ('P', 'Pending'),('E', 'Error'),('A', 'Aproved'),
            ('O', 'Aproved with Observations'),('R', 'Rejected'),
        ], string='DNIT Status', default='P', readonly=True,tracking=True, copy=False)
    
    l10n_py_dnit_ws_response_protaut  = fields.Char(string="Protocolo de autorizacion", readonly=True, tracking=True, copy=False)
    l10n_py_dnit_ws_response_codres = fields.Char(string="Codigo de respuesta", readonly=True, tracking=True, copy=False)
    l10n_py_dnit_ws_response_msgres = fields.Char(string="Mensaje de respuesta", readonly=True, tracking=True, copy=False)

    l10n_py_dnit_ws_request_json = fields.Text(string="JSON de envio", readonly=True, copy=False)
    l10n_py_dnit_ws_request_xml = fields.Text(string="XML de envio", readonly=True, copy=False)
    l10n_py_dnit_ws_response_json = fields.Text(string="JSON de respuesta", readonly=True, copy=False)

    l10n_py_dnit_ws_random_code = fields.Char(string='Random Code', 
        readonly=True, store=True, index = True,tracking=True, copy=False)

    def _get_l10n_py_dnit_ws_url( self, key):
        sKey = 'l10n_py_edi.url.' + key + '.test' if self.company_id.l10n_py_dnit_ws_environment == 'testing' else '.prod'

        ICP = self.env['ir.config_parameter'].sudo()
        sRet = str(ICP.get_param(sKey))
        return sRet

    # Buttons
    def _post(self, soft=True):
        py_invoices = self.filtered(lambda x: x.is_invoice() and x.country_code == "PY")
        sale_py_invoices = py_invoices.filtered(lambda x: x.move_type in ['out_invoice', 'out_refund'])

        # Verify only Vendor bills (only when verification is configured as 'required')
        #(py_invoices - sale_py_invoices)._l10n_ar_check_afip_auth_verify_required()

        # Send invoices to DNIT and get the return info
        py_edi_invoices = py_invoices.filtered(lambda x: x.journal_id.l10n_py_dnit_pos_system in ('RLI_RLM','AURLI_RLM','BFERCEL','FEERCEL','CPERCEL'))
        validated = error_invoice = self.env['account.move']
        for inv in py_edi_invoices:

            validated += super(AccountMove, inv)._post(soft=soft)

            ### La llamada a la SET
            #return_info = inv._l10n_ar_do_afip_ws_request_cae(client, auth, transport)
            return_info = inv._l10n_py_do_dnit_ws_request()
            if return_info:
                _logger.error( "Error de la SET: %s" % str(inv.l10n_py_dnit_ws_request_json))
                error_invoice = inv
                validated -= inv
                break

            # If we get CAE from AFIP then we make commit because we need to save the information returned by AFIP
            # in Odoo for consistency, this way if an error ocurrs later in another invoice we will have the ones
            # correctly validated in AFIP in Odoo (CAE, Result, xml response/request).
            #if not self.env.context.get('l10n_py_invoice_skip_commit'):
            self._cr.commit()

        if error_invoice:
            if error_invoice.exists():
                msg = _('We couldn\'t validate the document "%(partner_name)s" (Draft Invoice *%(invoice)s) in DNIT',
                    partner_name=error_invoice.partner_id.name, invoice=error_invoice.id)
            else:
                msg = _('We couldn\'t validate the invoice in DNIT.')
            msg += _('This is what we get:\n%s\n\nPlease make the required corrections and try again', str(return_info) + self.l10n_latam_document_number)

            # if we've already validate any invoice, we've commit and we want to inform which invoices were validated
            # which one were not and the detail of the error we get. This ins neccesary because is not usual to have a
            # raise with changes commited on databases
            if validated:
                unprocess = self - validated - error_invoice
                msg = _(
                    """Some documents where validated in DNIT but as we have an error with one document the batch validation was stopped

* These documents were validated:
%(validate_invoices)s
* These documents weren\'t validated:
%(invalide_invoices)s
""",
                    validate_invoices="\n   * ".join(validated.mapped('name')),
                    invalide_invoices="\n   * ".join([
                        _('%(item)s: "%(partner)s" amount %(amount)s', item=item.display_name, partner=item.partner_id.name, amount=item.amount_total_signed) for item in unprocess
                    ])
                )
            raise UserError(msg)

        return validated + super(AccountMove, self - py_edi_invoices)._post(soft=soft)


    def _l10n_py_do_dnit_ws_request(self):
        """ Submits the invoice information to DNIT and gets a response of DNIT in return.

        If we receive a positive response from  DNIT then validate the invoice and save the returned information in the
        corresponding invoice fields:

        * CDC number (Authorization Electronic Code)
        * Authorization Type
        * JSON Request
        * XML Request
        * JSON Response
        * Result (Approved, Aproved with Observations)

            NOTE: If there are observations we leave a message in the invoice message chart with the observation.

        If there are errors it means that the invoice has been Rejected by DNIT and we raise an user error with the
        processed info about the error and some hint about how to solve it. The invoice is not valided.
        """
        ##all_data = self._prepare_l10n_py_ws_data()
        all_data = libpyedi.get_xmlgen_DE(self)
        self.l10n_py_dnit_ws_request_json = all_data
        response = requests.post(
            self._get_l10n_py_dnit_ws_url("recibe"),  json=json.loads(json.dumps(all_data)), allow_redirects=False)
        if response.status_code == 301:
            response = requests.post( response.headers['Location'],  json=json.loads(json.dumps(all_data)))
        if response.status_code != 200:
            _logger.error( "Error: %s" % str(response.status_code))
            self.l10n_py_dnit_ws_response_estres = 'E'
            self.l10n_py_dnit_ws_response_fecproc = datetime.now()
            self.l10n_py_dnit_ws_response_cdc = None
            self.l10n_py_dnit_ws_response_digval = None
            self.l10n_py_dnit_ws_response_protaut = None
            self.l10n_py_dnit_ws_response_codres = str(response.status_code)
            self.l10n_py_dnit_ws_response_msgres = response.text
            self.l10n_py_dnit_ws_request_xml = None
            self.l10n_py_dnit_ws_response_json = None
            self.l10n_py_dnit_qr = None
            return str(response.status_code) + "-" + response.text

        self.l10n_py_dnit_ws_response_fecproc = datetime.now()
        self.l10n_py_dnit_ws_response_cdc = None
        self.l10n_py_dnit_ws_response_digval = None
        self.l10n_py_dnit_ws_response_protaut = None
        self.l10n_py_dnit_ws_response_codres = None
        self.l10n_py_dnit_ws_response_msgres = None
        self.l10n_py_dnit_ws_request_xml = None
        self.l10n_py_dnit_ws_response_json = response.text
        self.l10n_py_dnit_qr = None
        return self._py_json_responseDNIT( response.text)


    def _py_json_responseDNIT( self, response_data):
        """
        Process the response from the DNIT
        """
        #response = response_data.json()
        response = response_data
        # {
        #   'dEstRes': E, A, O, R
        #   'dCodRes': 0 o 260 o otro numero
        #   'dMsgRes': Mensaje de error
        #   'dId': CDC
        #   'dFecProc': Fecha en modo texto
        #   'dEstResDet':  Aprobado, Aprobado con observaciones, Rechazado
        #   'dProtAut': Codigo que no se para que sirve
        # }
        #self.l10n_py_dnit_ws_response_json = json.dumps(response, indent=4)
        self.l10n_py_dnit_ws_response_fecproc = datetime.now()

        response_value = libpydnitws.process_response_dnit( response)
        if response_value.get('dEstRes') == 'E':
            self.l10n_py_dnit_ws_response_estres = 'E'
            self.l10n_py_dnit_ws_response_codres = response_value.get('dCodRes')
            self.l10n_py_dnit_ws_response_msgres = response_value.get('dMsgRes')
            msg = "Error: " + str(response_value.get('dCodRes')) + " " + str(response_value.get('dMsgRes'))
            self.message_post(body=msg, message_type='notification')
            return response_value

        self.l10n_py_dnit_ws_response_cdc = response_value.get('dId')
        self.l10n_py_dnit_ws_response_fecproc = datetime.strptime(str(response_value.get('dFecProc')), "%Y-%m-%dT%H:%M:%S")  
        self.l10n_py_dnit_ws_response_estres = response_value.get('dEstRes')
        self.l10n_py_dnit_ws_response_codres = response_value.get('dCodRes')
        self.l10n_py_dnit_ws_response_msgres = response_value.get('dMsgRes')
        self.l10n_py_dnit_ws_response_protaut = response_value.get('dProtAut')

        self.l10n_py_dnit_qr = response_value.get('qr')

        if response_value.get('dEstRes') == None or response_value.get('dEstRes') == 'R':
            msg = "Warning: Documento " + str(response_value.get('dEstResDet')) + "\n[" + str(response_value.get('dCodRes')) + "-" + str(response_value.get('dMsgRes')) + "] "
            return response_value

        msg = "Success: Documento " + str(response_value.get('dEstResDet')) + "\n[" + str(response_value.get('dCodRes')) + "-" + str(response_value.get('dMsgRes')) + "] "
        return False

    @api.depends('l10n_py_dnit_ws_response_estres')
    def _compute_show_reset_to_draft_button(self):
        """
            EXTENDS 'account.move'
            When the DNIT approved the move, don't show the reset to draft button
        """
        super()._compute_show_reset_to_draft_button()
        self.filtered(lambda move: move.l10n_py_dnit_ws_response_estres == "A" or move.l10n_py_dnit_ws_response_estres == "O").show_reset_to_draft_button = False

    l10n_py_dnit_show_print_button = fields.Boolean(compute="_compute_show_button", store=False)

    @api.depends('journal_id')
    def _compute_show_button( self):
        for rec in self:
            if rec.journal_id.l10n_py_dnit_pos_system and rec.journal_id.l10n_py_dnit_pos_system in ('RLI_RLM','AURLI_RLM'):
                rec.l10n_py_dnit_show_print_button = True
            else:
                rec.l10n_py_dnit_show_print_button = False

    def action_mostrar_factura( self):
        base_url = self._get_l10n_py_dnit_ws_url("kude") + "/?"
        params = {
            'empresa': self.company_id.partner_id.vat.split("-")[0],
            'id': self.l10n_py_dnit_ws_response_cdc
        }
        encoded_params = urllib.parse.urlencode(params)
        full_url = base_url + encoded_params
        return {
            'type': 'ir.actions.act_url',
            'url': full_url,
            'target': 'new',
        }

    def action_print_pdf(self):
        if self.l10n_py_dnit_show_print_button:
            return self.action_mostrar_factura()
        return super().action_print_pdf()

    def action_invoice_sent(self):
        if self.l10n_py_dnit_show_print_button:
            return self.action_mostrar_factura()
        return super().action_invoice_sent()

