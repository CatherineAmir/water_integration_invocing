from odoo import fields, models, api, exceptions, _
from datetime import datetime, date
import datetime as dt
from odoo.exceptions import Warning, UserError, ValidationError, AccessError
import tempfile
import binascii
import xlrd
import logging
import itertools
import requests

_logger = logging.getLogger(__name__)
import cx_Oracle

import json

class BulkImport(models.Model):
    _name = 'sita_inv.huge_import'
    _description = 'Get From Query And Create Invoice '
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order='name desc'

    name = fields.Date(string='Invoice Date',compute='_month_name_compute',inverse='_month_name_compute',store=True)
    month=fields.Selection([('1','1'),('2','2'),('3','3'),('4','4'),('5','5'),('6','6'),('7','7'),
                            ('8','8'),('9','9'),('10','10'),('11','11'),('12','12')],string="Invoice by Month",compute='_month_name_compute',inverse='_month_name_compute',store=True)

    sheet_date = fields.Datetime(string="Creation Date",
                                 default=lambda self: datetime.now().strftime("%Y-%m-%d %H:%M:%S"), readonly=True)

    state = fields.Selection(selection=[('not_imported', 'Not Imported'),
                                        ('partially_imported', 'Partially Imported'),
                                        ('completely_imported', 'Completely Imported')], default='not_imported',
                             copy=False)
    invoice_type=fields.Selection([('invoice','Invoice'),('discount','Discount')],default='invoice',string='Invoice Type')

    active = fields.Boolean(default=True, string='Active')
    file = fields.Binary('File')

    database_set = fields.Selection(
        [('customer_service','Customer Service'),
        ('consumption','Consumption'),('prepaid','Prepraid')], default=lambda self: self.env.company.database_type,
        string='Database Set')

    summary_ids_posted = fields.One2many('sita.inv_summary', 'import_id', string='Invoice States',
                                         domain=[('state', '!=', 'not_imported')])
    summary_ids_not_imported = fields.One2many('sita.inv_summary', 'import_id', string='Invoice States',
                                               domain=[('state', '=', 'not_imported')])

    total_invoices = fields.Integer('Total Invoices', compute="_compute_numbers", store=True)
    total_posted = fields.Integer('Total Imported Invoice', compute="_compute_numbers", store=True)
    total_not_imported = fields.Integer('Total Not imported', compute="_compute_numbers", store=True)
    error_dict = {}
    data=[]
    total_number_of_invoices=fields.Integer('Total number of invoices in DB')
    total_number_of_lines=fields.Integer('Total number of invoice lines in DB')



    _sql_constraints = [
        ('unique_import_date',
         'unique(name,invoice_type)',
         'Import Date must be unique for the same type'),

    ]

    @api.depends('month','name')
    def _month_name_compute(self):
        pass
        # for r in self:
        #
        #
        #     if r.name and (r.database_set!='consumption' or r.invoice_type!='invoice' and r.database_set=='consumption'):
        #         r.month=str(r.name.month)
        #
        #     if r.month and r.database_set=='consumption' and r.invoice_type=='invoice':
        #         y=datetime.today().year
        #
        #         r.name=date(y,int(r.month),1)
        #
        #
        #


    @api.constrains('name')
    def check_date(self):
        for r in self:
            if r.name > date.today():
                raise ValidationError(
                    _("Invoice Date cannot be in the future"))

    @api.depends('summary_ids_posted', 'summary_ids_not_imported')
    def _compute_numbers(self):
        for r in self:
            r.total_not_imported = len(r.summary_ids_not_imported)
            r.total_posted = len(r.summary_ids_posted)
            r.total_invoices = len(r.summary_ids_posted + r.summary_ids_not_imported)
            r.adjust_state()

    @api.onchange('summary_ids_posted', 'summary_ids_not_imported')
    def compute_numbers(self):
        for r in self:
            r._compute_numbers()

    # this function should be replaced by query connector
    def connect_database(self, dataset, my_date, domain,imported):
        pass


    def cal_imported(self):
        imported = self.summary_ids_posted
        all_imported = []
        for im in imported:
            all_imported.append(im.name)
        # _logger.info('all_imported %s',all_imported)
        return all_imported

    def first_import(self):
        self.message_post(body="Start importing")

        data_to_test = self.connect_database(self.database_set, self.name, [],[])
        


        self.error_dict.clear()
        self.create_summary(data_to_test['INVOICE ID'],data_to_test['Customer Name'])
        self.test_all(data_to_test)
    
    
    
    
    def partially_import(self,not_imported=None):
        self.message_post(body="Continue importing importing")
        imported=self.cal_imported()


        names = []
        if not not_imported:
            not_imported = self.summary_ids_not_imported
        for n in not_imported:
            names.append(str(n.name))
        # _logger.info('domain_names %s', names)
        data_to_test = self.connect_database(self.database_set, self.name, names,imported)
        # logger.info('data_to_test %s',json.dumps(data_to_test))
        self.error_dict.clear()
        self.create_summary(data_to_test['INVOICE ID'],data_to_test['Customer Name'])
        
        self.test_all(data_to_test)

    def one_import(self, name):
        imported = self.cal_imported()
        names=[]
        names.append(str(name))
        data_to_test = self.connect_database(self.database_set, self.name,names,imported)

        self.error_dict.clear()
        self.create_summary(str(data_to_test['INVOICE ID']),data_to_test['Customer Name'])
        self.env['sita.inv_summary'].sudo().search([('name','=',str(name))]).error=False
        
        # _logger.info('error in after update summary %s',self.env['sita.inv_summary'].sudo().search([('name','=',str(name))]).error)
        self.test_all(data_to_test)

    def exceptional_import(self):
        self.partially_import()
    def get_invoices_discount(self):
        self.invoice_type='discount'
        self.partially_import()

    def create_summary(self, inv_names,inv_cust):
        
        inv_cust=list(set(inv_cust))
        # _logger.info('len inv_cust %s',len(list(set(inv_cust))))
        # _logger.info('len inv_names %s',len(list(set(inv_names))))
        all_summary = []
        
        
        for i in self.data:
            one_summary = []
            one_summary.append(str(i['INVOICE ID']).split('.')[0])
            
            one_summary.append('not_imported')
           
            one_summary.append(str(self.name).split('.')[0])
            one_summary.append(str(self.sheet_date))
            one_summary.append('True')
            one_summary.append(str(i['Customer Name']))
            
            one_sum = '~~'.join(one_summary)
            all_summary.append(one_sum)

        all_summeries = '|'.join(all_summary)
        cr = self.env.cr
        cr.execute("select batch_create_summary(%s)", (all_summeries,))
        cr.commit()
        cr.savepoint()
        

    def manage_error(self, column_name, cell_value, error_message, inv_id=None):


        # _logger.info('in manage_error function %s', self.error_dict)
        error_part = {'column_name': column_name,
                      'value': cell_value,
                      'error_message': error_message}

        if inv_id:
            ###print('in if inv_id')

            if str(inv_id).split('.')[0] in [k for k in self.error_dict.keys()]:
                pass

            else:
                self.error_dict.update({str(inv_id).split('.')[0]: []})
            if error_part in self.error_dict[str(inv_id).split('.')[0]]:
                ###print('error is exist before for the same invoice')
                pass
            else:

                self.error_dict[str(inv_id).split('.')[0]].append(error_part)
                ###print('error is will be appended ')
        else:
            ###print('invoice_id in error message is not exist')

            for l in self.data:

                # _logger.info('column_name %s', column_name)

                # if cell_value in [str(v).split('.')[0] for v in l.values()] or cell_value in l.values():
                if cell_value == l[column_name]:

                    if str(l['INVOICE ID']).split('.')[0] in [k for k in self.error_dict.keys()]:
                        pass

                    else:
                        self.error_dict.update({str(l['INVOICE ID']).split('.')[0]: []})

                    if error_part in self.error_dict[str(l['INVOICE ID']).split('.')[0]]:
                        ###print('seem_to_be_exist')
                        pass
                    else:
                        ###print('seem_to_be not_exist lets append')

                        self.error_dict[str(l['INVOICE ID']).split('.')[0]].append(error_part)

    def test_all(self, data_to_tested):

        cur = self.env.cr
       
        self.env.cr.commit()

        self.env.cr.savepoint()
        # _logger.info('data_to_tes t%s',json.dumps(data_to_tested))
        # _logger.info('data %s',json.dumps(self.data))
        # ###print('before test error dict', self.error_dict)
        _logger.info('start_test')
        self.test_invoice_name(cur, data_to_tested['INVOICE ID'])
        self.test_invoice_type_related_invoice(cur, data_to_tested['Invoice Type'],
                                               data_to_tested['Related Invoice'])
        self.test_product_code(cur, data_to_tested['Product Code'])

        self.test_customer_country(cur, data_to_tested['Country Code'])
        self.test_customer(cur, data_to_tested['INVOICE ID'], data_to_tested['Customer Name'],
                           data_to_tested['company person'],
                           data_to_tested['Country Code'],
                           data_to_tested['State'], data_to_tested['City'], data_to_tested['Street'],
                           data_to_tested['Building Number'], data_to_tested['National ID'],
                           data_to_tested['Passport ID'], data_to_tested['Tax ID'])
        self.test_branch_code(cur, data_to_tested['Branch Code'])
        self.test_activity_code(cur, data_to_tested['Activity Code'])
        self.test_data_time(data_to_tested['Date Issued'], data_to_tested['Time Issued'])

        self.test_unit(cur, data_to_tested['Unit'])
        self.test_customer_currency(cur, data_to_tested['Customer Currency'])
        self.test_taxes(cur, data_to_tested['Taxes Codes'])
        self.test_fixed_discount(cur, data_to_tested['Invoice Discount(fixed)'])
        self.test_quantity(cur, data_to_tested['Quantity'])
        self.test_customer_price(cur, data_to_tested['Customer Price'])

        self.test_line_discount(cur, data_to_tested['Discount(%)(line)'])
        self.test_create_exchange_rate(cur, data_to_tested['Exchange Rate'], data_to_tested['Customer Currency'],
                                       data_to_tested['Date Issued'])
        self.test_fixed_discount(cur, data_to_tested['Fixed Discount After Tax'])
        _logger.info('end_test')
        self.env.cr.commit()
        self.env.cr.savepoint()
        all_inv = list(set(data_to_tested['INVOICE ID']))

        all_inv_adj = [str(i).split('.')[0].strip() for i in all_inv]
        
        self.fast_create(all_inv_adj)
        return

    def fast_create(self, all_inv):

        inv_data, line_data = self.adjust_data()
        
        self.create_invoice(inv_data)
        _logger.info('invoices created')
        

        self.create_inv_lines(line_data)
        _logger.info('invoices line created')

        self.adjust_lines(all_inv)
        _logger.info('line_adjusted')
        self.adjust_invs(all_inv)
        _logger.info('invs_adjusted')
        self.adjust_summary(all_inv)
        self.compute_numbers()
        _logger.info('summary adjusted')
        self.adjust_state()
        _logger.info('adjust_state')
        

        self.env.cr.commit()
        self.env.cr.savepoint()
        _logger.info('import done')
        self.env.user.notify_success("import is done", sticky=False)
        return

    def adjust_state(self):
        if self.total_invoices == 0:
            self.state = 'not_imported'
        else:
            if self.total_invoices == self.total_posted:
                self.state = 'completely_imported'
            elif self.total_invoices == self.total_not_imported:
                self.state = 'not_imported'
            else:
                self.state = 'partially_imported'

    def create_invoice(self, inv_data):

        cr = self.env.cr
        cr.execute("select batch_create_invoice(%s)", (inv_data,))

    def create_inv_lines(self, line_data):

        cr = self.env.cr
        cr.execute("select line_create(%s)", (line_data,))

    def adjust_lines(self, all_inv):

        inv_lines = self.env['account.move.line'].search([('move_name', 'in', all_inv)])

        for l in inv_lines:
            l.get_fixed_discount()
            l._compute_sub_after()
            l._compute_total_after()
            l._onchange_price_subtotal()

    def adjust_invs(self, all_inv):
        invs = self.env['account.move'].search([('name', 'in', all_inv)])
        for r in invs:
            # _logger.info('r_in adjust invs',)

            r._compute_totals()
            r._compute_known_person()
            flag = 0
            if r.known_person == True and r.partner_id.customer_type == 'P':
                # ###print('person_id_required')
                if not r.national_id:
                    error_message = "This Customer Must Have national ID"
                    self.manage_error('National_ID', '', error_message, r.name)
                    flag = 1

                if not r.governorate:
                    error_message = "Governorate value must exist",
                    self.manage_error('Governorate', '', error_message, r.name)
                    flag = 1

                if not r.city:
                    error_message = "City value must exist",
                    self.manage_error('City', '', error_message, r.name)
                    flag = 1

                if not r.street:
                    error_message = "street value must  exist",
                    self.manage_error('street', '', error_message, r.name)
                    flag = 1

                if not r.street2:
                    error_message = "Building Number value must exist",
                    self.manage_error('Building Number', '', error_message, r.name)
                    flag = 1
            if flag:
                delete_from = """
                delete from account_move where id =%s
                """
                cur = self.env.cr
                cur.execute(delete_from, (r.id,))

    def adjust_summary(self, names):

        # ###print(self.error_dict)
        all_sum = self.env['sita.inv_summary'].search([('import_id', '=', self.id),('name','in',names)])

        for s in all_sum:

            for k in self.error_dict.keys():

                if s.name == k:

                    formatted_error = ''
                    for e in self.error_dict[k]:
                        formatted_error = formatted_error + '- Column Name :' + str(e['column_name']) + '\n' + \
                                          '- Value :' + str(e['value']) + '\n' + '- Error Message :' + str(
                            e['error_message']).replace('(', '').replace(')', '') + '\n' + '\n'

                    s.error = formatted_error
            s._get_all_invoices()
            if s.invoice_counts:
                s.state = 'draft'

    def adjust_data(self):

        invoice_data = []
        invoice_line_data = []
        write_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        user_id = self.env.user.id
        # _logger.info('self.error_dict.keys %s', self.error_dict.keys())
        # ###print('errors_invs', self.error_dict.keys())
        for l in self.data:
            if str(l['INVOICE ID']).split('.')[0] not in self.error_dict.keys():
                # _logger.info('invoice_id to be inserted',str(l['INVOICE ID']).split('.')[0])
                # ###print('dict',l)
                mydate = self.check_date(l['Date Issued'])
                mytime = self.check_time(l['Time Issued'])
                if mydate and mytime:

                    string_datetime = str(mydate) + ' ' + str(mytime)

                    datetime_obj = datetime.strptime(string_datetime, '%Y-%m-%d %H:%M:%S')

                    result_utc_datetime = datetime_obj - dt.timedelta(hours=2)
                    result_utc_datetime.strftime("%Y-%m-%d %H:%M:%S")

                    disc = str(l['Discount(%)(line)'])
                    if disc == '':
                        disc = '0'
                    disc_inv = str(l['Invoice Discount(fixed)'])
                    if disc_inv == '':
                        disc_inv = '0'

                    disc_after_tax = str(l['Fixed Discount After Tax'])
                    if disc_after_tax == '':
                        disc_after_tax = '0'

                    value_diff = str(l['Value Difference'])
                    if value_diff == '':
                        value_diff = '0'
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
                    vals.append(write_date)
                    vals.append(str(user_id))
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
                    invoice_line_data_vals.append(str(l['Product Desc']))
                    invoice_line_data_vals.append(value_diff)
                    invoice_line_data_vals.append(disc_after_tax)
                    invoice_line_data_vals.append(write_date)
                    invoice_line_data_vals.append(str(user_id))

                    one_line = '~~'.join(invoice_line_data_vals)
                    invoice_line_data.append(one_line)

                else:
                    pass
            else:
                pass

        final_data_inv = '|'.join(invoice_data)
        final_inv_lin = '|'.join(invoice_line_data)

        return final_data_inv, final_inv_lin

    def test_invoice_name(self, cur, inv_name):
        names = list(set(inv_name))
        query_inv = """
        select id from account_move where name=%s and state Not IN ('invalid')
        """
        for n in names:
            cur.execute(query_inv, (str(n).split('.')[0],))
            invoice = cur.fetchone()

            if invoice == None:
                pass

            else:
                error_message = "Invoice ID in sheet shouldn't be exist in the odoo database or exist in invalid state only"
                self.manage_error('INVOICE ID', str(n).split('.')[0], error_message)
                # raise ValidationError(("inovice id in sheet shouldn't be exist in the odoo database or exist in draft state only ,the prpblem is in Invoice Id ",n))

    def test_invoice_type_related_invoice(self, cur, invoice_type, related_invoice):

        search_related_inv = """
                          select id from account_move where name = %s and state='valid' limit 1
                          """

        invoices = list(set(invoice_type))
        r_inv = list(set(related_invoice))

        for i in invoices:
            if i.strip() == 'Invoice' or i.strip() == 'Credit Note' or i.strip() == 'Debit Note':
                pass

            else:
                error_message = "Invoice Type Value must be equal 'Invoice'  or 'Credit Note'  or  'Debit Note'"
                self.manage_error('Invoice Type', i.strip(), error_message)

        for r in r_inv:
            if r == '':
                pass
            else:

                cur.execute(search_related_inv, (str(r).split('.')[0]), )
                inv = cur.fetchone()

                if inv != None:
                    pass
                else:

                    error_message = "Related Invoice name must be exist in the database with valid state",
                    self.manage_error('Invoice Type', r, error_message)

    def get_product_from_api(self, product_code):
        # ###print('in_get_product_api')
        """
        this function get all the product details from the portal using ths EGS standard code or GS1 code
        :param product_code:
        https://sdk.preprod.invoicing.eta.gov.eg/api/27-get-code-details-by-item-code/

        insert the product in database using sql connection
        :return:True if product is found False : else
        """

        #
        token = self.env.company.get_token()
        preplink = self.env.company.api_link

        try:
            header = \
                {
                    'Accept': "application/json",
                    'Accept-Language': "en",
                    'Content-type': "application/json",
                    'Authorization': 'Bearer ' + token,
                }
        except Exception:
            return False

        if str(product_code)[0:2] == 'EG':
            codeType = 'EGS'
            p_code = str(product_code)[13:]
        else:
            codeType = 'GS1'
            product_code = str(product_code).split('.')[0]
            p_code = product_code

        url = preplink + "/api/v1.0/codetypes/" + codeType + "/codes/" + str(product_code)

        try:
            getting_all = requests.get(url, headers=header, verify=False)


        except Exception:
            return False

        if getting_all.status_code == 200:
            my_code = getting_all.json()

            act_f = datetime.strptime(my_code['activeFrom'], '%Y-%m-%dT%H:%M:%SZ')
            active_from = act_f.strftime('%Y-%m-%d %H:%M:%S')

            active = my_code['active']
            if active == False:
                state = 'in'
            else:
                state = 'a'

            if my_code['activeTo'] == None:

                code_create = """
                                insert into product_template(code_type,name,name_in_arabic,description_en,description_ar,active_from,standard_code,product_code,state,sale_ok,type,categ_id,uom_id,uom_po_id,active)
                                 values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                                 RETURNING id

                                """
                cur = self.connect_odoo()
                cur.execute(code_create,
                            (codeType, my_code['codeName'], my_code['codeNameAr'], my_code['description'],
                             my_code['descriptionAr'],
                             active_from, my_code['itemCode'], p_code,
                             state, True, 'consu', 1, 1, 1, True))
                id = cur.fetchone()
            else:
                act_t = datetime.strptime(my_code['activeTo'], '%Y-%m-%dT%H:%M:%SZ')
                active_to = act_t.strftime('%Y-%m-%d %H:%M:%S')
                code_create = """
                insert into product_template(code_type,name,name_in_arabic,description_en,description_ar,active_from,active_to,standard_code,product_code,state,sale_ok,type,categ_id,uom_id,uom_po_id,active)
                 values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                 RETURNING id

                """
                cur = self.connect_odoo()
                cur.execute(code_create,
                            (codeType, my_code['codeName'], my_code['codeNameAr'], my_code['description'],
                             my_code['descriptionAr'],
                             active_from, active_to, my_code['itemCode'], p_code,
                             state, True, 'consu', 1, 1, 1, True))
                id = cur.fetchone()

            product_product = """
            insert into product_product(product_tmpl_id,active) values(%s,%s)
            """
            cur = self.connect_odoo()
            cur.execute(product_product,
                        (id, True))

            return True

        else:
            return False

    def connect_odoo(self):
        cr = self.env.cr
        return cr

    def test_product_code(self, cur, product_code):

        search_code = """
              select id from product_template where standard_code = %s limit 1
                  """

        products = list(set(product_code))

        for p in products:

            cur.execute(search_code, (str(p).strip().split('.')[0],))
            curr = cur.fetchone()

            if curr != None:
                pass
            else:
                product_mapper = """
                select code from product_map where name=%s limit 1
                """
                cur.execute(product_mapper, (str(p).strip().split('.')[0],))
                curr = cur.fetchone()
                if curr != None:
                    pass
                else:
                    flag = self.get_product_from_api(str(p).strip().split('.')[0])
                    if not flag:
                        # ###print('product error')
                        error_message = "product code must be  in standard code",
                        self.manage_error('Product Code', str(p).strip().split('.')[0], error_message)

    def test_customer_country(self, cur, country_code):
        """
           function check the existance of the country code in table res_country
           :param cur:
           :param country_code:
           :return: no return
       """

        search_countries = """
                       select id from res_country where code = %s limit 1
                       """
        countries = list(set(country_code))
        for c in countries:

            cur.execute(search_countries, (c,))
            coun = cur.fetchone()

            if coun != None:
                pass
            else:

                error_message = "Customer Country must be exist in ISO standard ",
                self.manage_error('Country Code', c, error_message)

    # this function need update
    def test_customer(self, cur, inv_ids, customer_name, company_person, country_code, state, city, street, buil_num,
                      national_id, pass_id, tax_id):
        """

                :param cur:
                :param customer_name:
                :param company_person:

                :param country_code: required
                the rest of the address paramters are required when the customer is company or the foreigner or the is person and the egyptian and the invoice total is larger
                50000
                :param state:
                :param city:
                :param street:
                :param buil_num:
                :param national_id: required for egyptian with  the egyptian and the invoice total is larger
                50000
                :param pass_id: required for foreigners
                :param tax_id:  required for company
                :return:
                """
        # _logger.info('inv_ids %s',json.dumps(inv_ids, ensure_ascii=False).encode('UTF-8'))
        unique_customers = list(customer_name)

        query_customer = """
        select id from res_partner where name = %s limit 1
        """

        create_query = """
        insert into res_partner (name,customer_type,display_name,is_company,governorate,city,street,street2,national_id,passport_id,vat,customer_rank,country_id,create_date,type,state,active)
        values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)

            RETURNING id;
        """

        update_query = """
             update  res_partner 
             set name=%s,
             customer_type=%s,
             display_name=%s,
             is_company=%s,
             governorate=%s ,
             city=%s,
             street=%s,
             street2=%s,
             national_id=%s,
             passport_id=%s,
             vat=%s,
             customer_rank=%s,
             country_id=%s,
             create_date=%s,
             type=%s,
             state=%s,
             active=%s 
             where id=%s;
                """

        for i in range(len(customer_name)):
            # _logger.info('customer_name[i] %s',json.dumps(customer_name[i], ensure_ascii=False).encode('UTF-8'))
            # _logger.info('inv_ids[i] %s',inv_ids[i])

            if company_person[i].lower() == 'person':
                is_company = False
            else:
                is_company = True
            country_query = """
                           select id from res_country where code=%s limit 1"""

            cur.execute(country_query, (country_code[i],))
            country = cur.fetchone()

            if company_person[i].lower() == 'company' and country != None:
                if country[0] == 65:
                    customer_type = 'B'
                else:
                    customer_type = 'F'
            elif company_person[i].lower() == 'person' and country != None:
                if country[0] == 65:
                    customer_type = 'P'
                else:
                    customer_type = 'F'
            else:
                customer_type = 'B'
            flag = 0

            if customer_type in ['B', 'F']:
                if not customer_name[i]:
                    error_message = "customer_name value must exist",
                    self.manage_error('customer_name', '', error_message, inv_id=inv_ids[i])

                    flag = 1
                

                if not state[i]:
                    error_message = "Governorate value must exist",
                    self.manage_error('Governorate', '', error_message, inv_id=inv_ids[i])

                    flag = 1

                if not city[i]:
                    error_message = "City value must exist",
                    self.manage_error('City', '', error_message, inv_ids[i])
                    flag = 1

                    # raise ValidationError(_("City value must exist the Issue is in invoice with name  %s ", r.name))

                if not street[i]:
                    error_message = "street value must exist",
                    self.manage_error('street', '', error_message, inv_ids[i])
                    flag = 1

                if not buil_num[i]:
                    error_message = "Building Number value must be exist",
                    self.manage_error('Building Number', '', error_message, inv_ids[i])
                    flag = 1

                if customer_type == 'B':
                    if not tax_id[i]:
                        error_message = "Tax id value must be exist",
                        self.manage_error('Tax Id', '', error_message, inv_ids[i])
                        flag = 1
                    elif len(str(tax_id[i]).split('.')[0].strip().replace(" ", "").replace("-", "").replace('_',
                                                                                                            "")) > 9:
                        error_message = "Tax id value must 9 digits",
                        self.manage_error('Tax Id', '', error_message, inv_ids[i])
                        flag = 1
                    elif not str(tax_id[i]).split('.')[0].strip().replace(" ", "").replace("-", "").replace('_',
                                                                                                            "").isdigit():
                        error_message = "Tax id value must 9 digits only ",
                        self.manage_error('Tax Id', tax_id[i], error_message, inv_ids[i])
                        flag = 1

                if customer_type == 'F':
                    if not pass_id[i]:
                        error_message = "passport Id value must be exist",
                        self.manage_error('passport Id ', '', error_message, inv_ids[i])
                        flag = 1


            else:
                pass
            if  flag:
                pass

            else:

                create_date = datetime.now()

                now = create_date.strftime("%Y-%m-%d %H:%M:%S")

                cur.execute(query_customer, (unique_customers[i],))
                curr = cur.fetchone()
                if curr != None:
                    # ###print(curr)
                    cur.execute(update_query, (
                        customer_name[i], customer_type, customer_name[i], is_company, state[i], city[i], street[i],
                        str(buil_num[i]).split('.')[0].strip().replace(" ", ""),
                        str(national_id[i]).split('.')[0].strip().replace(" ", ""),
                        str(pass_id[i]).split('.')[0].strip().replace(" ", ""),
                        str(tax_id[i]).split('.')[0].strip().replace(" ", "").replace("-", "").replace('_', ""), 1,
                        country,
                        now,
                        'contact', 'draft', True, curr[0]))

                    # ###print('customer_updated with id',curr)
                    my_partner = self.env['res.partner'].search([('id', '=', curr[0])])
                    my_partner._check_your_vat()
                    my_partner._compute_id()
                    self.env.cr.commit()
                    self.env.cr.savepoint()



                else:

                    cur.execute(create_query, (
                        customer_name[i], customer_type, customer_name[i], is_company, state[i], city[i], street[i],
                        str(buil_num[i]).split('.')[0].strip().replace(" ", ""),
                        str(national_id[i]).split('.')[0].strip().replace(" ", ""),
                        str(pass_id[i]).split('.')[0].strip().replace(" ", ""),
                        str(tax_id[i]).split('.')[0].strip().replace(" ", "").replace("-", "").replace('_', ""), 1,
                        country,
                        now, 'contact', 'draft', True))
                    id = cur.fetchone()

                    my_partner = self.env['res.partner'].search([('id', '=', id[0])])

                    my_partner._check_your_vat()
                    my_partner._compute_id()
                    self.env.cr.commit()
                    self.env.cr.savepoint()

    def test_branch_code(self, cur, brs):
        """
        check the existance of the branches in the inv_branches table
        :param cur:
        :param brs: branch codes to be searched in inv_branches table
        :return: error if the branch doesn't exist
        """
        search_branch = """
                     select id from inv_branch where code = %s limit 1
                       """
        br = list(set(brs))
        for b in br:
            cur.execute(search_branch, (str(b).split('.')[0],))
            branch = cur.fetchone()

            if branch != None:
                pass
            else:
                error_message = "Branch Code must be as Branch Code in the Configuration menu",
                self.manage_error('Branch Code', str(b).split('.')[0], error_message)

    def test_activity_code(self, cur, act):
        """
      check the existance of the branches in the inv.activity.code table
      :param cur:
      :param act: activity codes to be searched in inv.activity.code table
      :return: error if the activity code doesn't exist
      """

        search_code = """
                         select id from inv_activity_code where code = %s and active=True limit 1
                       """
        acts = list(set(act))

        for a in acts:
            cur.execute(search_code, (str(a).split('.')[0],))
            act_code = cur.fetchone()

            if act_code != None:

                pass
            else:

                error_message = "Activity Code must be as Activity Code in the Configuration menu",
                self.manage_error('Activity Code', str(a).split('.')[0], error_message)

    def check_date(self, mydate):
        """
               function check the date format and reformat it in YYYY-mm-dd
               :param mydate:
               :return:date in string format
        """
        try:
            datetime_date = xlrd.xldate_as_datetime(mydate, 0)
            string_date = datetime_date.strftime('%Y-%m-%d')


        except Exception:

            try:
                datetime_date = datetime.strptime(mydate, '%d-%m-%Y')
                string_date = datetime_date.strftime('%Y-%m-%d') 
                return string_date  
            except Exception:
                try:
                    datetime_date = datetime.strptime(mydate, '%d-%m-%y')
                    string_date = datetime_date.strftime('%Y-%m-%d')
                    return string_date
                except Exception:
                    try:
                        datetime_date = datetime.strptime(mydate, '%d/%m/%y')
                        string_date = datetime_date.strftime('%Y-%m-%d')
                        return string_date
                    except Exception:
                        try:
                            datetime_date = datetime.strptime(mydate, '%d/%m/%Y')
                            string_date = datetime_date.strftime('%Y-%m-%d')
                            return string_date
                        except Exception:
                            error_message = "Wrong Date Format. Date Should be Typically as your system date format",
                            self.manage_error('Date Issued', mydate, error_message)

    def check_time(self, mytime):
        """
       function check time format to be 24 hours hh:mm:ss
       :param mytime:time to be reformated
       :return: time in string format
       """

        try:
            datetime_time = xlrd.xldate_as_datetime(mytime, 0)
            time_object = datetime_time.time()
            # ###print('time_object1', time_object)

            string_time = time_object.isoformat()

            return string_time


        except Exception:
            try:
                my_str = str(mytime).strip()
                my_time = datetime.strptime(my_str, ' %I:%M:%S %p')
                ###print('my_time', my_time)

                string_time = my_time.strftime('%H:%M:%S')
                ###print('string_time', string_time)

                return string_time

            except Exception:
                try:
                    my_str = str(mytime).strip()
                    ###print('my_str', my_str)

                    my_time = datetime.strptime(my_str, '%H:%M:%S')

                    string_time = my_time.strftime('%H:%M:%S')
                    ###print('string_time', string_time)

                    return string_time

                except Exception:

                    error_message = "Wrong Time Format. Time Should be in format HH:MM:SS",
                    self.manage_error('Time Issued', mytime, error_message)

    def test_data_time(self, my_date, my_time):
        """
       function call test function for date and test function for time
       :param my_date:
       :param my_time:
       :return:
       """

        line_date = list(set(my_date))

        line_time = list(set(my_time))

        x = list(map(self.check_date, line_date))
        y = list(map(self.check_time, line_time))

    def test_unit(self, cur, units):
        """
     check the existance of the units in the inv.units table
     :param cur:
     :param units: units to be searched in iinv.units table
     :return: error if the unit doesn't exist
         """

        search_unit = """
                           select id from inv_units where code = %s and active=True limit 1
                       """
        unit = list(set(units))
        for u in unit:
            cur.execute(search_unit, (u,))
            curr = cur.fetchone()

            if curr != None:
                pass
            else:

                error_message = "product unit must be as in configuration menu",
                self.manage_error('Unit', u, error_message)

    def test_customer_currency(self, cur, currency):
        """
        function check the existance in of customer currency in res_currency_table
        :param cur:
        :param currency: currency to be checked
        :return: error if currency doesn't exist
        """

        search_currency = """
                               select id from res_currency where name = %s and active= True limit 1
                               """
        currencies = list(set(currency))
        for c in currencies:
            cur.execute(search_currency, (c,))
            curr = cur.fetchone()

            if curr != None:
                pass
            else:
                error_message = """Customer Currency  active  must be exist in ISO standard 
                                 and must be active form the configuration menu"""
                self.manage_error('Customer Currency', c, error_message)
                # raise ValidationError(
                #     _("Customer Currency  active  must be exist in ISO standard and must be active form the configuration menu, the problem is in Currency with name %s", c))

    def test_taxes(self, cur, my_taxes):
        taxes = []
        for t in my_taxes:
            tax = t.strip().replace(" ", "")
            tax = tax.replace('-', "")
            tax = tax.replace('/', "")

            one_tax = tax.split(',')
            for one in one_tax:
                # ###print('one_tax', one_tax)
                taxes.append(one)

        check_taxes = list(set(taxes))
        get_taxes = """
        select id from account_tax where code=%s and active=True and type_tax_use='sale' and vendor_name is null limit 1
        """

        for t in check_taxes:
            if t == "":
                pass
            else:

                cur.execute(get_taxes, (t,))
                curr = cur.fetchone()

                if curr != None:
                    pass
                else:
                    error_message = "Tax code  must be exist configuration menu and activated"
                    self.manage_error('Tax code', t, error_message)



    def test_fixed_discount(self, cur, fixed_discount):
        disc = list(set(fixed_discount))
        for d in disc:
            if d == '':
                pass
            else:
                try:
                    d = float(d)

                except ValueError:
                    error_message = "fixed discount value must a positive number"
                    self.manage_error('fixed discount', d, error_message)
                    # raise ValidationError(_("fixed discount value must a positive number %s",d))

                if float(d) < 0:
                    error_message = "fixed discount value must be positive number"
                    self.manage_error('fixed discount', d, error_message)
                    # raise ValidationError(_("fixed discount value must be positive number the problem is with value %s",d))

    def test_quantity(self, cur, quantity):
        quan = list(set(quantity))
        for q in quan:

            try:
                q = float(q)
            except ValueError:
                error_message = "Quantity value must a positive number"
                self.manage_error('Quantity', q, error_message)

            if float(q) < 0 or float(q) == 0:
                error_message = "Quantity value must be positive number"
                self.manage_error('Quantity', q, error_message)

    def test_customer_price(self, cur, prices):
        price = list(set(prices))
        for p in price:

            try:
                p = float(p)
            except ValueError:
                error_message = "Price value must a positive number"
                self.manage_error('Customer Price', p, error_message)

            if float(p) < 0 or float(p) == 0:
                error_message = "Customer Price must a positive number"
                self.manage_error('Tax code', p, error_message)

    def test_line_discount(self, cur, discount):

        disc = list(set(discount))
        for d in disc:
            if d == '':
                pass
            else:
                try:
                    d = float(d)
                except ValueError:
                    error_message = "line discount  must be a percentage from 0 t0 100"
                    self.manage_error('Line discount', d, error_message)

                if d < 0 or d > 100:
                    error_message = "line discount  must be a percentage from 0 t0 100"
                    self.manage_error('Line discount', d, error_message)

    def test_create_exchange_rate(self, cur, rate, curr, date_iss):
        
        
        company_id = self.env.company.id
        all_data = []
        for r in range(0, len(date_iss)):
            line_data = []
            line_data.append(date_iss[r])
            line_data.append(curr[r])
            try:
                myrate = float(rate[r])
            except Exception:
                if curr[r] == 'EGP':
                    myrate = 1
                else:
                    error_message = "Exchange rate can't be empty if the currency is not EGP"
                    self.manage_error('Exchange rate', ' ', error_message)
                    # raise ValidationError(_("Exchange rate can't be empty if the currency is not EGP"))

            line_data.append(myrate)
            all_data.append(line_data)

        all_data.sort()
        set_line_date = list(num for num, _ in itertools.groupby(all_data))

        exchange_rate_create = """
        insert into res_currency_rate(name,rate,currency_id,company_id) values(%s,%s,%s,%s)
        """
        search_query = """
        select rate from res_currency_rate where currency_id =%s and name=%s
        """
        currency_query = """ select id from res_currency where name =%s
        """
        for rec in set_line_date:
            acc_date = self.check_date(rec[0])

            curr = rec[1]
            r = rec[2]

            cur.execute(currency_query, (curr,))
            currency = cur.fetchone()
            if currency == None:
                error_message = "currency  doesn't exist"
                self.manage_error('Currency', curr, error_message)
                # raise ValidationError(_("currency with name %s doesn't exist",curr))
            else:
                if acc_date == None:

                    error_message = "date format error"
                    self.manage_error('Date Issued', rec[0], error_message)
                else:
                    cur.execute(search_query, (currency, acc_date))
                    my_rate = cur.fetchone()

                    if my_rate == None:
                        cur.execute(exchange_rate_create, (acc_date, r, currency, company_id,))

                    elif my_rate[0] != r:
                        
                        error_message = "only one Currency rate per day is allowed"
                        self.manage_error('Exchange Rate', curr, error_message)

                    else:
                        pass


class InvSummary(models.Model):
    _name = 'sita.inv_summary'
    _description = 'Short Summary for invoices'
    _order='name desc'

    name = fields.Char('Invoice Name', required=True)
    customer_name = fields.Char('Customer Name', required=False)
    state = fields.Selection(
        selection=[('not_imported', 'Not Imported'), ('draft', 'draft'),('posted', 'Posted'), ('pending', 'Pending'), ('valid', 'Valid'),
                   ('invalid', 'Invalid'), ('cancel', 'Cancelled'),('waiting','Waiting')])

    import_id = fields.Many2one('sita_inv.huge_import', required=True, string='Import ID')

    invoice_date = fields.Datetime('Import Date', related='import_id.sheet_date', store=True)
    active = fields.Boolean(default=True, string='Active')

    error = fields.Text('Error message')

    account_move_ids = fields.Many2many('account.move', compute='_get_all_invoices', store=True, )
    invoice_counts = fields.Integer(compute='_get_all_invoices', store=True,string='invoices')

    def import_one_invoice(self):
        self.import_id.one_import(self.name)
        
    def server_action_import(self):
       
        grouped=self.read_group([('state','=','not_imported'),('id','in',self.ids)],fields=['import_id'],groupby=['import_id'])    
       
        for group in grouped:
           
            self.env['sita_inv.huge_import'].search([('id','=',group['import_id'][0])]).partially_import(self.search([('import_id','=',group['import_id'][0]),('state','=','not_imported'),('id','in',self.ids)]))
        
        

    def get_all_invoices(self):
        action = self.env.ref('sita-e-invoicing.sita_action_move_out_invoice_type').read()[0]
        action['domain'] = ['|', ('name', '=', self.name), ('related_id.name', '=', self.name)]
        return action

    @api.depends('state')
    def _get_all_invoices(self):
        for r in self:
            
            r.account_move_ids = self.env['account.move'].sudo().with_context(active_test=False).search(
                ['|', ('name', '=', r.name), ('related_id.name', '=', r.name)])

            r.invoice_counts = len(r.account_move_ids)
            if r.invoice_counts:
                pass
            else:
                r.invoice_counts=0
                r.state='not_imported'

    @api.onchange('account_move_ids')
    def adjust_summary_states(self):
        self._adjust_summary_states()

    @api.depends('account_move_ids', 'account_move_ids.state')
    def _adjust_summary_states(self):
        _logger.info('in _adjust_summary_states')
        for r in self:
            r._get_all_invoices()
            if not  r.invoice_counts and not  r.account_move_ids:
                r.state = 'not_imported'
            elif r.account_move_ids and r.invoice_counts:
                latest_id = max(r.account_move_ids.ids)
                move = self.env['account.move'].search([('id', '=', latest_id)])

                r.state = move.state


            else:
                _logger.info('something went error')
    
    def adjust_this_states(self):
       
        for r in self:
            
            r._get_all_invoices()
            if not  r.invoice_counts:
                r.state = 'not_imported'
            elif r.account_move_ids and r.invoice_counts:
                latest_id = max(r.account_move_ids.ids)
                move = self.env['account.move'].search([('id', '=', latest_id)])
                
                r.state = move.state
               

            else:
                _logger.info('something went error')
                

    @api.model
    def init(self):
        self.env.cr.execute("""

                    DROP FUNCTION IF EXISTS batch_create_summary (TEXT);
                    CREATE or REPLACE FUNCTION batch_create_summary(data TEXT)
                    RETURNS VOID AS $BODY$
                    DECLARE

                    records TEXT[];
                    inv_rec TEXT[];
                    rec TEXT;
                    move_exist integer;
                    v_inv_no TEXT;
                    my_state TEXT;
                    my_date integer;
                    cust_name TEXT;
                    create_date timestamp without time zone;

                    activated BOOL;


                    BEGIN
                        SELECT string_to_array(data,'|')INTO records;
                        foreach rec in ARRAy records LOOP
                            SELECT String_to_array(rec,'~~') INTO inv_rec;
                            v_inv_no=inv_rec[1];
                            my_state=inv_rec[2];
                            my_date=(select id from sita_inv_huge_import where name=(SELECT TO_DATE(inv_rec[3],'YYYY-MM-DD') order by id desc limit 1)order by id desc limit 1);
                            create_date=inv_rec[4];
                            activated=inv_rec[5];
                            cust_name=inv_rec[6];




                        select id from sita_inv_summary where name=v_inv_no into move_exist ;
                        if move_exist is NULL THEN
                            insert into sita_inv_summary(name,state,import_id,invoice_date,active,customer_name,error)
                           
                                                 values(v_inv_no,my_state,my_date,create_date,activated,cust_name,null);
                        else 
                         update sita_inv_summary 
                         set error = NULL,
                         customer_name=cust_name
                         
                         where name=v_inv_no;


                        END IF;


                        END LOOP;
                    END;

                    $BODY$
                    LANGUAGE plpgsql;

                            """)
