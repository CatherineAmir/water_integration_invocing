from odoo import models, fields, api, _

from odoo.exceptions import ValidationError
import subprocess
from decimal import Decimal
import json
from asn1crypto import cms, util, algos, x509, core, pem, keys, tsp
# import pkcs11
# from pkcs11 import Attribute, ObjectClass, KeyType, UserAlreadyLoggedIn
import time
from datetime import datetime, date, timedelta
import pytz

import base64

import logging

_logger = logging.getLogger(__name__)

# tt='D:/SITA/CustomModules/sita-e-invoicing/models'

class MyCompany(models.Model):
    # _inherit = [,, ]
    _inherit = ['res.company']

    # 'mail.thread',



    # is_water=fields.Boolean(string='Is multi database Company',default=False)
    # multi_company_server=fields.Boolean(string='Multi Company Server',default=False)

    database_type=fields.Selection([('customer_service','Customer Service'),
                                    ('consumption','Consumption'),('prepaid','Prepraid')],
                                   string='Database Type',default='customer_service')

