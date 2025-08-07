-- disable l10n_py_account DNIT integration
UPDATE res_company
   SET l10n_py_dnit_ws_environment = 'testing';
