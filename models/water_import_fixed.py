from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError, AccessError
import logging
import cx_Oracle
from datetime import datetime, date
import datetime as dt
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class Company(models.Model):
    _inherit = 'res.company'

    special_customer = fields.Boolean(default=False)
    database_type = fields.Selection(selection_add=[('operation_for_other', 'Operation for Others')],
                                     ondelete={'operation_for_other': 'set default'})

    @api.model
    def init(self):
        self.env.cr.execute("""
              ALTER TABLE  res_company 
          ADD COLUMN  IF not EXISTS special_customer Boolean
              """)


import json


class BulkImportFixedTax(models.Model):
    _inherit = 'sita_inv.huge_import'
    database_set = fields.Selection(
        [('customer_service', 'Customer Service'), ('consumption', 'Consumption'), ('prepaid', 'Prepraid'),
         ('operation_for_other', 'Operation For Others')],
        default=lambda self: self.env.company.database_type, string='Database Set')

    special_customer = fields.Boolean(default=lambda self: self.env.company.special_customer)

    @api.depends('month', 'name')
    def _month_name_compute(self):
        for r in self:

            if r.name and (
                    r.database_set != 'consumption'):
                r.month = str(r.name.month)

            if r.month and r.database_set == 'consumption':
                y = datetime.today().year

                r.name = date(y, int(r.month), 1)


    def connect_database(self, dataset, my_date, domain, imported):
        _logger.info('domain %s', domain)
        ip = 'orarac-scan.mcwwgov.local'
        _logger.info('in the inherited connect')
        _logger.info('my_date %s', my_date)

        port = 1521
        SID = 'orcl'
        try:
            cx_Oracle.init_oracle_client(lib_dir=r"D:\instantclient_21_3")
        except Exception as e:
            # _logger.info('error %s',e)
            pass

        try:
            dsn_tns = cx_Oracle.makedsn(ip, port, service_name=SID)
        except Exception as e:
            raise AccessError(_("Can't Connect to Oracle DB %s", e))

        username = 'mnftax'
        password = 'mnftax'
        try:
            conn = cx_Oracle.connect(username, password, dsn_tns)

        except  Exception as e:
            raise AccessError(_("Cann't login into the Oracle database %s", e))
        
        invoices_ids=[]
        if dataset == 'consumption':

            if self.invoice_type == 'invoice':
                if self.special_customer:

                    view_name = "BILLELEC_TAXD"
                else:

                    view_name = "BILLELEC_TAX"

                query = """
                              select INVOICE_ID,
                              INVOICE_TYPE,
                              RELATED_INVOICE,
                              CUSTOMER_NAME,
                              COMPANY_PERSON,
                              COUNTRY_CODE,
                              STATE,
                              CITY,
                              STREET,
                              BUILDING_NO,
                              NATIONAL_ID,
                              PASSPORT_ID,
                              TAX_ID,
                              BRANCH_CODE,
                              ACTIVITY_CODE,
                              DATE_ISSUE,
                              TIMME_ISSUED,
                              INVOICE_DISCOUNT,
                              PRODUCT_CODE,
                              '',
                              QUANTITY,
                              UNIT,
                              CUSTOMER_CURRENCY,
                              EXCHANGE_RATE,
                              PRICE,
                              DISCOUNT,
                              TAX_CODE,
                              '',
                              ''
                              from {view:}
                              where
                              to_date(date_issue, 'dd/mm/rrrr') = to_date(:mydate, 'dd/mm/rrrr')

                           """.format(view=view_name)
                _logger.info('ready to connect consumption invoice')

                cursor = conn.cursor()
                # _logger.info("Query %s", query)
                cursor.execute(query, mydate=str(my_date.strftime('%d/%m/%Y')))
                res = cursor.fetchall()
                # self.message_post(body="invoices in res {}".format(set(res).join(","))
                # _logger.info('res %s',json.dumps(res))
                # _logger.info('len res consumption description %s', len(res))

                columns = cursor.description
            else:
                query_1 = """

                  select INVOICE_ID,
                  INVOICE_TYPE,
                  RELATED_INVOICE,
                  CUSTOMER_NAME,
                  COMPANY_PERSON,
                  COUNTRY_CODE,
                  STATE,
                  CITY,
                  STREET,
                  BUILDING_NO,
                  NATIONAL_ID,
                  PASSPORT_ID,
                  TAX_ID,
                  BRANCH_CODE,
                  ACTIVITY_CODE,
                  DATE_ISSUE,
                  TIMME_ISSUED,
                  INVOICE_DISCOUNT,
                  PRODUCT_CODE,
                  '',
                  QUANTITY,
                  UNIT,
                  CUSTOMER_CURRENCY,
                  EXCHANGE_RATE,
                  PRICE,
                  DISCOUNT,
                  TAX_CODE,
                  '',
                  ''
                  from billelec_tax_discount 
                  where


                   to_date(date_issue, 'dd/mm/rrrr') >= to_date(:mydate, 'dd/mm/rrrr') and
                    to_date(date_issue, 'dd/mm/rrrr') <= to_date(:mydate2, 'dd/mm/rrrr')
                   """

                query_2 = """

                                  select INVOICE_ID,
                                  INVOICE_TYPE,
                                  RELATED_INVOICE,
                                  CUSTOMER_NAME,
                                  COMPANY_PERSON,
                                  COUNTRY_CODE,
                                  STATE,
                                  CITY,
                                  STREET,
                                  BUILDING_NO,
                                  NATIONAL_ID,
                                  PASSPORT_ID,
                                  TAX_ID,
                                  BRANCH_CODE,
                                  ACTIVITY_CODE,
                                  DATE_ISSUE,
                                  TIMME_ISSUED,
                                  INVOICE_DISCOUNT,
                                  PRODUCT_CODE,
                                  '',
                                  QUANTITY,
                                  UNIT,
                                  CUSTOMER_CURRENCY,
                                  EXCHANGE_RATE,
                                  PRICE,
                                  DISCOUNT,
                                  TAX_CODE,
                                  '',
                                  ''
                                  from billelec_tax_add 
                                  where

                                to_date(date_issue, 'dd/mm/rrrr') >= to_date(:mydate, 'dd/mm/rrrr') and
                                to_date(date_issue, 'dd/mm/rrrr') <= to_date(:mydate2, 'dd/mm/rrrr')
                                   """

                # _logger.info('ready to connect discount')
                # _logger.info('my date %s', str(my_date.strftime('%d/%m/%Y')))

                cursor = conn.cursor()
                cursor.execute(query_1, mydate=str(my_date.strftime('%d/%m/%Y')),
                               mydate2=str((my_date + relativedelta(day=31)).strftime('%d/%m/%Y')))
                res_1 = cursor.fetchall()
                cursor.execute(query_2, mydate=str(my_date.strftime('%d/%m/%Y')),
                               mydate2=str((my_date + relativedelta(day=31)).strftime('%d/%m/%Y')))

                res_2 = cursor.fetchall()

                _logger.info('Connection Done')

                res = res_1 + res_2
                self.message_post(body="invoices in res {}".format(set(res).join(",")))

                # _logger.info('res %s',json.dumps(res))
                # _logger.info('len res %s', len(res))

                columns = cursor.description
        else:
            ip = 'orarac-scan.mcwwgov.local'

            if not ip:
                raise ValidationError(_('There is No  IP address to connect'))


            else:
                port = 1521
                SID = 'orcl'
                try:
                    cx_Oracle.init_oracle_client(lib_dir=r"C:\instantclient_21_3")
                except Exception as e:
                    # _logger.info('error %s',e)
                    pass

                try:
                    dsn_tns = cx_Oracle.makedsn(ip, port, service_name=SID)
                except Exception as e:
                    raise AccessError(_("Can't Connect to Oracle DB %s", e))

                username = 'mnftax'
                password = 'mnftax'
                try:
                    conn = cx_Oracle.connect(username, password, dsn_tns)
                # print(conn.version)
                except  Exception as e:
                    raise AccessError(_("Cann't login into the Oracle database %s", e))

                if dataset == 'customer_service':
                    view_name = 'CSELEC_TAX'
                else:
                    view_name = 'CSELEC_TAX_CRPS'

                query = """select INVOICE_ID,
                   INVOICE_TYPE,
                   RELATED_INVOICE,
                   CUSTOMER_NAME,
                   COMPANY_PERSON,
                   COUNTRY_CODE,
                   STATE,
                   CITY,
                   STREET,
                   BUILDING_NO,
                   NATIONAL_ID,
                   PASSPORT_ID,
                   TAX_ID,
                   BRANCH_CODE,
                   ACTIVITY_CODE,
                   DATE_ISSUE,
                   TIMME_ISSUED,
                   INVOICE_DISCOUNT,
                   PRODUCT_CODE,
                   '',
                   QUANTITY,
                   UNIT,
                   CUSTOMER_CURRENCY,
                   EXCHANGE_RATE,
                   PRICE,
                   DISCOUNT,
                   TAX_CODE,
                   '',
                   ''


                   from {view:}

                   where   
                   to_date(date_issue,'dd/mm/rrrr')= to_date(:mydate,'dd/mm/rrrr')""".format(view=view_name)
                _logger.info('ready to connect')

                cursor = conn.cursor()
                # try:
                cursor.execute(query, mydate=str(my_date.strftime('%d/%m/%Y')))
                _logger.info('Connection Done')

                res = cursor.fetchall()
                # self.message_post(body="invoices in res {}".format(set(res).join(","))
                # _logger.info('res %s',json.dumps(res))
                # _logger.info('len res %s', len(res))
                self.total_number_of_invoices=len(list(set(res[i][0] for i in range(len(res)))))
                 ##logger.info('res invoice names %s',self.total_number_of_invoices)
                self.total_number_of_lines=len(res)
                self.env.cr.commit()
                self.env.cr.savepoint()

                columns = cursor.description
            # conn.close()
        # _logger.info('ROWS %s', res[0])

        first_row = ['INVOICE ID', 'Invoice Type', 'Related Invoice', 'Customer Name', 'company person',
                     'Country Code',
                     'State', 'City', 'Street', 'Building Number', 'National ID', 'Passport ID', 'Tax ID',
                     'Branch Code',
                     'Activity Code', 'Date Issued', 'Time Issued', 'Invoice Discount(fixed)', 'Product Code',
                     'Product Desc', 'Quantity',
                     'Unit', 'Customer Currency', 'Exchange Rate', 'Customer Price', 'Discount(%)(line)',
                     'Taxes Codes', 'Value Difference', 'Fixed Discount After Tax']

        self.data.clear()
        product_taxes = {'EG-266662870-1527': 'OF04', 'EG-266662870-854': 'OF02'}
        taxes_mapped = []

        for row in range(0, len(res)):
            invoices_ids.append(str(res[row][0]))
            if domain:
                if str(res[row][0]) not in domain or str(res[row][0]) in imported:
                    if len(domain):
                        _logger.info('res[row][0] not in domain %s', res[row][0])
                        continue

            if str(res[row][18]) in product_taxes.keys():
                p_dict = {'Invoice ID': str(res[row][0]), 'Fixed Tax': product_taxes[res[row][18]],
                          'Fixed Tax Amount': res[row][24]}
                # print('p_dict',p_dict)
                taxes_mapped.append(p_dict)
                continue
            elm = {}
            for col in range(0, len(res[row])):

                if col == 0:
                    if str(res[row][0]) in imported:
                        _logger.info('in imported')
                        continue

                    elm[first_row[col]] = str(res[row][col])
                    # _logger.info('invoice_id %s', str(res[row][col]))


                elif str(first_row[col]) == 'Branch Code':
                    elm[first_row[col]] = 0


                elif first_row[col] == 'Date Issued':
                    elm[first_row[col]] = datetime.strptime(res[row][col], '%d/%m/%Y').strftime('%d-%m-%Y')
                    # _logger.info('date _issued %s', datetime.strptime(res[row][col], '%d/%m/%Y').strftime('%d-%m-%Y'))



                else:

                    elm[first_row[col]] = res[row][col] or ''
            if str(res[row][0]) not in imported:
                # _logger.info('added element in data')
                elm['Fixed Tax'] = ''
                elm['Fixed Tax Amount'] = ''
                self.data.append(elm)
            # print('taxes_mapped',taxes_mapped)

        self.add_tax_to_data(taxes_mapped)

        # print('data',data)
        self.message_post(body="invoices names={}".format(invoices_ids))
        data_to_test = {}
        for col in range(0, len(first_row)):

            getted_rows = []

            for row in range(0, len(res)):
                if domain:
                    if str(res[row][0]) not in domain or str(res[row][0]) in imported:
                        continue
                if col == 0:
                    # _logger.info('str(res[row][col] %s',str(res[row][col]))
                    getted_rows.append(str(res[row][col]))

                elif first_row[col] == 'Branch Code':
                    getted_rows.append(0)
                elif first_row[col] == 'Date Issued':
                    getted_rows.append(datetime.strptime(res[row][col], '%d/%m/%Y').strftime('%d-%m-%Y'))
                else:

                    getted_rows.append(res[row][col] or '')

            data_to_test[first_row[col]] = getted_rows
        # _logger.info('data_to_tested %s', data_to_test)
        # _logger.info('dataa %s',json.dumps(self.data))
        # _logger.info('domain %s', domain)
        # _logger.info('data %s', self.data)

        conn.close()
        # _logger.info('data ready to test len data %s', len(self.data))
        return data_to_test

    def add_tax_to_data(self, mapped_tax):
        if self.data:
            for t in mapped_tax:
                search_id = t['Invoice ID']
                # print('search_id',search_id)
                data_matched = list(filter(
                    lambda inv: inv['INVOICE ID'] == search_id and inv['Fixed Tax'] == '' and inv[
                        'Fixed Tax Amount'] == '',
                    self.data))
                # print('data_matched',data_matched)

                if len(data_matched):
                    # print(len(data_matched))

                    l = data_matched[0]
                    ind = self.data.index(l)
                    # _logger.info('index %s', ind)
                    self.data[ind]['Fixed Tax'] = t['Fixed Tax']
                    self.data[ind]['Fixed Tax Amount'] = t['Fixed Tax Amount']
                    # print('data updated',data[ind])
                    # print('\n')
                    # print('data',data)
                else:
                    pass

                    # raise ValidationError(_("some fixed taxes haven't beed allocated to lines ,%s", search_id))

    def adjust_data(self):

        invoice_data = []
        invoice_line_data = []
        print('errors_invs', self.error_dict.keys())
        for l in self.data:
            if str(l['INVOICE ID']).split('.')[0] not in self.error_dict.keys():
                # print('dict',l)
                mydate = self.check_date(l['Date Issued'])
                mytime = self.check_time(l['Time Issued'])
                if mydate and mytime:

                    string_datetime = str(mydate) + ' ' + str(mytime)

                    datetime_obj = datetime.strptime(string_datetime, '%Y-%m-%d %H:%M:%S')

                    result_utc_datetime = datetime_obj - dt.timedelta(hours=2)
                    result_utc_datetime.strftime("%Y-%m-%d %H:%M:%S")

                    disc = str(l['Discount(%)(line)'])
                    # _logger.info('disc_is BEFORE "%s"', disc)
                    if disc.strip() == '':
                        disc = '0'
                    # _logger.info('disc_is AFTER "%s"', disc)
                    disc_inv = str(l['Invoice Discount(fixed)'])
                    if disc_inv.strip() == '':
                        disc_inv = '0'
                    disc_after_tax = str(l['Fixed Discount After Tax'])
                    if disc_after_tax.strip() == '':
                        disc_after_tax = '0'

                    value_diff = str(l['Value Difference'])
                    if value_diff.strip() == '':
                        value_diff = '0'

                    fixed_tax = str(l['Fixed Tax Amount']) if str(l['Fixed Tax Amount']).strip() != '' else '0'
                    vals = []
                    invoice_line_data_vals = []
                    vals.append(str(l['INVOICE ID']).split('.')[0].strip())
                    vals.append(str(l['Invoice Type'][0]).split('.')[0].strip())
                    vals.append(str(l['Related Invoice']).split('.')[0].strip())
                    vals.append(str(l['Customer Name']))
                    vals.append(str(l['Branch Code']).split('.')[0].strip().replace(" ", ""))
                    vals.append(str(l['Activity Code']).split('.')[0].strip().replace(" ", ""))
                    vals.append(str(result_utc_datetime))
                    vals.append(disc_inv)
                    vals.append('draft')  # state
                    vals.append('True')  # active
                    vals.append('out_invoice')
                    vals.append('True')  # custom sequnece
                    vals.append('False')  # system_sequence
                    vals.append('1')  # journal_id
                    vals.append(str(mydate))
                    vals.append(str(self.env.ref('base.main_company').currency_id.id))
                    vals.append(str(self.env.company.id))
                    one_inv = '~~'.join(vals)
                    invoice_data.append(one_inv)

                    # invoice_line_data
                    invoice_line_data_vals.append(str(l['INVOICE ID']).split('.')[0])  # move_name
                    invoice_line_data_vals.append(str(self.env.company.id))
                    invoice_line_data_vals.append(str(self.env.ref('base.main_company').currency_id.id))

                    invoice_line_data_vals.append(str(l['Product Code']).strip().split('.')[0])
                    invoice_line_data_vals.append(str(l['Quantity']))
                    invoice_line_data_vals.append(str(l['Unit']))
                    invoice_line_data_vals.append(str(l['Customer Currency']))
                    invoice_line_data_vals.append(str(l['Customer Price']))
                    invoice_line_data_vals.append(str(l['Taxes Codes']))

                    invoice_line_data_vals.append(str(mydate))
                    invoice_line_data_vals.append(disc)
                    invoice_line_data_vals.append(str(l['Fixed Tax']))
                    # _logger.info('fixed_tax %s', str(l['Fixed Tax']))
                    invoice_line_data_vals.append(fixed_tax)
                    invoice_line_data_vals.append(str(l['Product Desc']))
                    invoice_line_data_vals.append(value_diff)
                    invoice_line_data_vals.append(disc_after_tax)

                    one_line = '~~'.join(invoice_line_data_vals)
                    invoice_line_data.append(one_line)
                else:
                    pass
            else:
                pass

        final_data_inv = '|'.join(invoice_data)
        final_inv_lin = '|'.join(invoice_line_data)
        # _logger.info('final_data_inv %s',json.dumps(final_data_inv))
        # _logger.info('final_inv_lin %s',json.dumps(final_inv_lin))
        _logger.info('data adjusted')
        return final_data_inv, final_inv_lin

    def create_inv_lines(self, line_data):

        cr = self.env.cr
        cr.execute("select line_create_fixed_tax(%s)", (line_data,))