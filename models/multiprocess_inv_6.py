import json
import time
import multiprocessing as mp

from .invoice import adjust_float, adjust_string
import os
import subprocess

import re
from datetime import datetime, timedelta

import requests
from psycopg2 import OperationalError, errorcodes, errors

from odoo import _
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError, AccessError
from multiprocessing import Value

t_num = 6

import logging

_logger = logging.getLogger(__name__)
tt = 'D:/sita/Odoo14/server/odoo/addons/sita-e-invoicing/models'
tokenfile_exe_1 = '/water_menofia_1.exe'
tokenfile_exe_2 = '/water_menofia_2.exe'
tokenfile_exe_3 = '/water_menofia_3.exe'
tokenfile_exe_4 = '/water_menofia_4.exe'
tokenfile_exe_5 = '/water_menofia_5.exe'
tokenfile_exe_6 = '/water_menofia_6.exe'

critical = None


class InvoiceMulti(models.Model):
    _inherit = "account.move"

    @staticmethod
    def serialize_and_sign_1(my_list, res, my_ids, failed, failed_ids, count_fail_1, db_name):
        count_fail_1.value = 0
        for i in range(0, len(my_list)):
            for j in range(0, 2):
                try:
                    my_sig = subprocess.run(
                        [tt + tokenfile_exe_1, db_name, str(my_ids[i])],
                        stdout=subprocess.PIPE)

                except Exception as e:
                    raise ValidationError(_("Something went wrong in digital signature %s", e))

                else:
                    if my_sig.stdout.decode('utf-8').startswith("Token") and j == 0:
                        time.sleep(1)
                    elif my_sig.stdout.decode('utf-8').startswith("Token") and j == 1:
                        count_fail_1.value = count_fail_1.value + 1

                        failed_ids.append(my_ids[i])
                        failed.append(my_list[i])
                    else:
                        my_signature = my_sig.stdout.decode('utf-8').rstrip()
                        signature = {
                            'signatureType': 'I',
                            'value': my_signature
                        }
                        my_list[i].update({'signatures': [signature]})

                        res.append(my_list[i])
                        break

    @staticmethod
    def serialize_and_sign_2(my_list, res, my_ids, failed, failed_ids, count_fail_2, db_name):
        count_fail_2.value = 0
        for i in range(0, len(my_list)):
            for j in range(0, 2):
                try:
                    my_sig = subprocess.run(
                        [tt + tokenfile_exe_2, db_name, str(my_ids[i])],
                        stdout=subprocess.PIPE)

                except Exception as e:
                    raise ValidationError(_("Something went wrong in digital signature %s", e))

                else:
                    if my_sig.stdout.decode('utf-8').startswith("Token") and j == 0:
                        time.sleep(1)
                    elif my_sig.stdout.decode('utf-8').startswith("Token") and j == 1:
                        count_fail_2.value = count_fail_2.value + 1

                        failed_ids.append(my_ids[i])
                        failed.append(my_list[i])
                    else:
                        my_signature = my_sig.stdout.decode('utf-8').rstrip()
                        signature = {
                            'signatureType': 'I',
                            'value': my_signature
                        }
                        my_list[i].update({'signatures': [signature]})

                        res.append(my_list[i])
                        break

    @staticmethod
    def serialize_and_sign_3(my_list, res, my_ids, failed, failed_ids, count_fail_3, db_name):
        count_fail_3.value = 0
        for i in range(0, len(my_list)):
            for j in range(0, 2):
                try:
                    my_sig = subprocess.run(
                        [tt + tokenfile_exe_3, db_name, str(my_ids[i])],
                        stdout=subprocess.PIPE)

                except Exception as e:
                    raise ValidationError(_("Something went wrong in digital signature %s", e))

                else:
                    if my_sig.stdout.decode('utf-8').startswith("Token") and j == 0:
                        time.sleep(1)
                    elif my_sig.stdout.decode('utf-8').startswith("Token") and j == 1:
                        count_fail_3.value = count_fail_3.value + 1

                        failed_ids.append(my_ids[i])
                        failed.append(my_list[i])
                    else:
                        my_signature = my_sig.stdout.decode('utf-8').rstrip()
                        signature = {
                            'signatureType': 'I',
                            'value': my_signature
                        }
                        my_list[i].update({'signatures': [signature]})

                        res.append(my_list[i])
                        break

    @staticmethod
    def serialize_and_sign_4(my_list, res, my_ids, failed, failed_ids, count_fail_4, db_name):
        count_fail_4.value = 0
        for i in range(0, len(my_list)):
            for j in range(0, 2):
                try:
                    my_sig = subprocess.run(
                        [tt + tokenfile_exe_4, db_name, str(my_ids[i])],
                        stdout=subprocess.PIPE)

                except Exception as e:
                    raise ValidationError(_("Something went wrong in digital signature %s", e))

                else:
                    if my_sig.stdout.decode('utf-8').startswith("Token") and j == 0:
                        time.sleep(1)
                    elif my_sig.stdout.decode('utf-8').startswith("Token") and j == 1:
                        count_fail_4.value = count_fail_4.value + 1

                        failed_ids.append(my_ids[i])
                        failed.append(my_list[i])
                    else:
                        my_signature = my_sig.stdout.decode('utf-8').rstrip()
                        signature = {
                            'signatureType': 'I',
                            'value': my_signature
                        }
                        my_list[i].update({'signatures': [signature]})

                        res.append(my_list[i])
                        break

    @staticmethod
    def serialize_and_sign_5(my_list, res, my_ids, failed, failed_ids, count_fail_5, db_name):
        count_fail_5.value = 0
        for i in range(0, len(my_list)):
            for j in range(0, 2):
                try:
                    my_sig = subprocess.run(
                        [tt + tokenfile_exe_5, db_name, str(my_ids[i])],
                        stdout=subprocess.PIPE)

                except Exception as e:
                    raise ValidationError(_("Something went wrong in digital signature %s", e))

                else:
                    if my_sig.stdout.decode('utf-8').startswith("Token") and j == 0:
                        time.sleep(1)
                    elif my_sig.stdout.decode('utf-8').startswith("Token") and j == 1:
                        count_fail_5.value = count_fail_5.value + 1

                        failed_ids.append(my_ids[i])
                        failed.append(my_list[i])
                    else:
                        my_signature = my_sig.stdout.decode('utf-8').rstrip()
                        signature = {
                            'signatureType': 'I',
                            'value': my_signature
                        }
                        my_list[i].update({'signatures': [signature]})

                        res.append(my_list[i])
                        break

    @staticmethod
    def serialize_and_sign_6(my_list, res, my_ids, failed, failed_ids, count_fail_6, db_name):

        count_fail_6.value = 0
        for i in range(0, len(my_list)):
            for j in range(0, 2):
                try:
                    my_sig = subprocess.run(
                        [tt + tokenfile_exe_6, db_name, str(my_ids[i])],
                        stdout=subprocess.PIPE)

                except Exception as e:
                    raise ValidationError(_("Something went wrong in digital signature %s", e))

                else:
                    if (my_sig.stdout.decode('utf-8').startswith("Token") or my_sig.stdout.decode(
                            'utf-8') == "") and j == 0:
                        time.sleep(1)

                    elif (my_sig.stdout.decode('utf-8').startswith("Token") or my_sig.stdout.decode(
                            'utf-8') == "") and j == 1:
                        count_fail_6.value = count_fail_6.value + 1

                        failed_ids.append(my_ids[i])
                        failed.append(my_list[i])

                    else:
                        my_signature = my_sig.stdout.decode('utf-8').rstrip()
                        signature = {
                            'signatureType': 'I',
                            'value': my_signature
                        }
                        my_list[i].update({'signatures': [signature]})

                        res.append(my_list[i])
                        _logger.info('res %s', res)

                        break

    def act_submit_invoice(self):
        start_all = datetime.now()
        _logger.info("start at %s", str(datetime.now()))
        # print('start_multi_import at', str(datetime.now()))
        c1 = 0
        c2 = 0
        c3 = 0
        c4 = 0
        c5 = 0
        c6 = 0
        _logger.info("len(self= %s)", len(self))

        if __name__ == "odoo.addons.sita-e-invoicing.models.multiprocess_inv_6":
            __spec__ = "ModuleSpec(name='builtins', loader=<class '_frozen_importlib.BuiltinImporter'>)"
            # _logger.info("start at %s", str(datetime.now()))

            if self.env.user.has_group('sita-e-invoicing.group_invoicing_senior_accountant'):
                pass
            else:
                raise AccessError(_("You are not allowed to submit invoices"))

            try:
                limit = 78
                for i in range(0, len(self), limit):
                    _logger.info("in first for loop i= %s", i)

                    if i + limit < len(self) or i + limit == len(self):
                        m = limit
                    else:
                        m = len(self) - i

                    z = []
                    inv_ids = []
                    startbatch = datetime.now()
                    _logger.info("startbatch at %s", str(datetime.now()))
                    self_ids = []
                    for b in range(i, i + m, 1):

                        global critical
                        critical = 0
                        r = self[b]
                        self_ids.append(r.id)

                        if r.state == 'posted':
                            inv_ids.append(r.id)

                            r._compute_known_person()
                            my_doc = r.prepare_invoice_dict()
                            r.string_inv = my_doc
                            self.env.cr.commit()
                            self.env.cr.savepoint()
                            z.append(my_doc)



                        else:
                            pass
                    # z_dumped = json.dumps(z, ensure_ascii=False).encode('UTF-8')
                    # _logger.info('z_dumped :%s', len(z_dumped))
                    t1 = 1
                    t2 = 1
                    t3 = 1
                    t4 = 1
                    t5 = 1
                    t6 = 1

                    # completely failed flag

                    with mp.Manager() as manager:

                        res = manager.list([])

                        while len(z) and critical < 4:
                            _logger.info('in while, z=%s', len(z))
                            token_string = str(t1) + str(t2) + str(t3) + str(t4) + str(t5) + str(t6)
                            ids, invs = token_algorithm(token_string, z, inv_ids)

                            # _logger.info('natural_list_ids %s', json.dumps(ids, ensure_ascii=False).encode('UTF-8'))
                            # _logger.info('natural_invs_list %s', json.dumps(invs, ensure_ascii=False).encode('UTF-8'))

                            # _logger.info('ids after_lists manager %s',ids)
                            # _logger.info('invs after_lists manager %s',invs)
                            failed = manager.list([])
                            failed_ids = manager.list([])
                            _logger.info('res= %s', len(res))
                            count_fail_1 = Value('i')
                            count_fail_2 = Value('i')
                            count_fail_3 = Value('i')
                            count_fail_4 = Value('i')
                            count_fail_5 = Value('i')
                            count_fail_6 = Value('i')

                            db_name = self.env.cr.dbname
                            _logger.info('db_name %s', db_name)
                            # _logger.info('ids [3],%s',ids[3])
                            # _logger.info('invs [3],%s',invs[3])
                            pro1 = mp.Process(target=self.serialize_and_sign_1,
                                              args=(invs[0], res, ids[0], failed, failed_ids, count_fail_1, db_name))
                            pro2 = mp.Process(target=self.serialize_and_sign_2,
                                              args=(invs[1], res, ids[1], failed, failed_ids, count_fail_2, db_name))
                            pro3 = mp.Process(target=self.serialize_and_sign_3,
                                              args=(invs[2], res, ids[2], failed, failed_ids, count_fail_3, db_name))
                            pro4 = mp.Process(target=self.serialize_and_sign_4,
                                              args=(invs[3], res, ids[3], failed, failed_ids, count_fail_4, db_name))
                            pro5 = mp.Process(target=self.serialize_and_sign_5,
                                              args=(invs[4], res, ids[4], failed, failed_ids, count_fail_5, db_name))
                            pro6 = mp.Process(target=self.serialize_and_sign_6,
                                              args=(invs[5], res, ids[5], failed, failed_ids, count_fail_6, db_name))
                            _logger.info('process are started')
                            pro1.start()
                            pro2.start()
                            pro3.start()
                            pro4.start()
                            pro5.start()
                            pro6.start()

                            pro1.join()
                            pro2.join()
                            pro3.join()
                            pro4.join()
                            pro5.join()
                            pro6.join()

                            _logger.info('process are ended')
                            _logger.info('len res in end %s', len(res))
                            _logger.info('len failed in end %s', len(failed))
                            # _logger.info(' tyeperes: {}'.format(type(res)))
                            _logger.info('res % ', json.dumps(list(res), ensure_ascii=False).encode('UTF-8'))
                            _logger.info('failed % ', json.dumps(list(failed), ensure_ascii=False).encode('UTF-8'))

                            _logger.info('1 %s', count_fail_1.value)
                            _logger.info('2 %s', count_fail_2.value)
                            _logger.info('3 %s', count_fail_3.value)
                            _logger.info('4 %s', count_fail_4.value)
                            _logger.info('5 %s', count_fail_5.value)
                            _logger.info('6 %s', count_fail_6.value)

                            z = list(failed)
                            inv_ids = list(failed_ids)
                            # _logger.info('z %s',json.)
                            # _logger.info('inv_ids %s', inv_ids)
                            t1 = 0 if int(count_fail_1.value) > len(invs[0]) // 2 else 1
                            t2 = 0 if int(count_fail_2.value) > len(invs[1]) // 2 else 1
                            t3 = 0 if int(count_fail_3.value) > len(invs[2]) // 2 else 1
                            t4 = 0 if int(count_fail_4.value) > len(invs[3]) // 2 else 1
                            t5 = 0 if int(count_fail_5.value) > len(invs[4]) // 2 else 1
                            t6 = 0 if int(count_fail_6.value) > len(invs[5]) // 2 else 1

                            c1 = 1 if int(count_fail_1.value) == len(invs[0]) and len(invs[0]) else c1
                            c2 = 1 if int(count_fail_2.value) == len(invs[1]) and len(invs[1]) else c2
                            c3 = 1 if int(count_fail_3.value) == len(invs[2]) and len(invs[2]) else c3
                            c4 = 1 if int(count_fail_4.value) == len(invs[3]) and len(invs[3]) else c4
                            c5 = 1 if int(count_fail_5.value) == len(invs[4]) and len(invs[4]) else c5
                            c6 = 1 if int(count_fail_6.value) == len(invs[5]) and len(invs[5]) else c6

                            t1 = 0 if c1 else t1
                            t2 = 0 if c2 else t2
                            t3 = 0 if c3 else t3
                            t4 = 0 if c4 else t4
                            t5 = 0 if c5 else t5
                            t6 = 0 if c6 else t6

                            # _logger.info('t1 %s', t1)
                            # _logger.info('t2 %s', t2)
                            # _logger.info('t3 %s', t3)
                            # _logger.info('t4 %s', t4)

                            # _logger.info('t5 %s', t5)
                            # _logger.info('t6 %s', t6)

                            _logger.info('not work c1 %s', c1)
                            _logger.info('not work c2 %s', c2)
                            _logger.info('not work c3 %s', c3)
                            _logger.info('not work c4 %s', c4)
                            _logger.info('not work c5 %s', c5)
                            _logger.info('not work c6 %s', c6)

                        my_res = list(res)
                        my_data = json.dumps(my_res, ensure_ascii=False).encode('UTF-8')
                        # _logger.info('my_data %s', my_data)
                        # _logger.info('my_res len %s', len(my_res))

                    if critical > 3:
                        raise ValidationError(
                            _("All the Tokens are not inserted,please insert them and reset waiting invoices to posted"))
                    _logger.info('signature_done', str(datetime.now()))

                    if len(my_res):
                        docs = {'documents': my_res}
                        _logger.info('len(docs) %s', len(docs))
                        # _logger.info('docs %s', docs)
                        self.submit_to_portal(docs, 1, self_ids)
                        _logger.info('submitted_to portal')
                        total_time = datetime.now() - startbatch
                        _logger.info("total_time for batch %s", str(total_time))
                    # time.sleep(4)

                else:
                    pass
            except  OperationalError as e:
                _logger.info('OperationalError')
                if e.pgcode == errorcodes.SERIALIZATION_FAILURE:
                    _logger.info('Serialization_failure %s tries', tries)
                    pass


            except errors.InFailedSqlTransaction as e:
                _logger.info('InFailedSqlTransaction')
                pass

            self.env.cr.savepoint()
            self.env.user.notify_success("Submission Done", sticky=True)
            if c1:
                self.env.user.notify_warning('Token 1 in not insterted  please plug it in the port',
                                             sticky=True)
            if c2:
                self.env.user.notify_warning('Token 2 in not insterted  please plug it in the port',
                                             sticky=True)

            if c3:
                self.env.user.notify_warning('Token 3 in not insterted  please plug it in the port',
                                             sticky=True)

            if c4:
                self.env.user.notify_warning('Token 4 in not insterted  please plug it in the port',
                                             sticky=True)
            if c5:
                self.env.user.notify_warning('Token 5 in not insterted  please plug it in the port',
                                             sticky=True)
            if c6:
                self.env.user.notify_warning('Token 6 in not insterted  please plug it in the port',
                                             sticky=True)

            total_time = datetime.now() - start_all
            _logger.info("total_time %s", str(total_time))


        else:
            raise ValidationError(_("Please Check Multiprocessing file name"))


def token_algorithm(token_string, invs, ids):
    invoices = []
    ids_division = []
    for tokens in range(len(token_string)):
        ids_division.append([])
        invoices.append([])

    ones = [i.start() for i in re.finditer('1', token_string)]

    if not len(ones):
        global critical
        critical = critical + 1
        ones = [i for i in range(len(token_string))]

    part = len(ids) // len(ones)
    for t in range(0, len(ones)):

        if t == len(ones) - 1:
            ids_division[ones[t]] = ids[t * part:]
            invoices[ones[t]] = invs[t * part:]

        else:
            ids_division[ones[t]] = ids[t * part:(t + 1) * part]
            invoices[ones[t]] = invs[t * part:(t + 1) * part]

    return ids_division, invoices