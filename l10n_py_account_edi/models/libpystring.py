#

from difflib import SequenceMatcher

_MOTEMI = {
    'DEVOLUCION Y AJUSTE DE PRECIOS':'1',
    'DEVOLUCION':'2',
    'DESCUENTO':'3',
    'BONIFICACION':'4',
    'CREDITO INCOBRABLE':'5',
    'RECUPERO DE COSTO':'6',
    'RECUPERO DE GASTO':'7',
    'AJUSTE DE PRECIO':'8',
    'CREDITO':'5',
    'INCOBRABLE':'5',
    'COSTO':'6',
    'GASTO':'7',
    'AJUSTE':'8',
    'PRECIO':'8',
}

_VALUES = {
    '1': 0.0,
    '2': 0.0,
    '3': 0.0,
    '4': 0.0,
    '5': 0.0,
    '6': 0.0,
    '7': 0.0,
    '8': 0.0,
}
def compare_strings(ref):
    """
    Compare two strings and return True if they are equal, False otherwise.
    """
    # ej. ref = Reversion de: FA-A 001-001-1234567, No se especifica
    val = _VALUES
    for texto in ref.upper().split(' '):   # ej. texto = 'ESPECIFICA'
        for notemi in _MOTEMI.keys():   # notemi = 'COSTO'
            key_values = _MOTEMI.get(notemi) or '0'  # ej. '6' - '1' - '8'
            ratio = SequenceMatcher(None, texto, notemi).ratio()  # ej. 0.8
            old_value = val.get(key_values) # ej. 0.0
            if old_value == None:
                continue
            old_value += ratio  # ej. 0.0 + 0.8
            val.update({ key_values : old_value})

    old_key = '0'
    for key, value in val.items():
        if value > (val.get(old_key) or 0.0):
            old_key = key
    return old_key
