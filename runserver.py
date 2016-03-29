# -*- coding: utf-8 -*-
"""
Bootstrap the Flask web application.
"""

from item_catalog import app

__author__ = 'Andres Anies'
__email__ = 'andres_anies@hotmail.com'

# Bootstrap the Flask Application.
app.run(host='0.0.0.0', port=5000, debug=True)
