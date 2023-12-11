from odoo import fields, models, api


class AccountMove(models.Model):
    _inherit = 'account.move'


    def create_invoice_batch(self):
        self.env.cr.execute("""

                            DROP FUNCTION IF EXISTS batch_create_invoice (TEXT);
                            CREATE or REPLACE FUNCTION batch_create_invoice(data TEXT)
                            RETURNS VOID AS $BODY$
                            DECLARE

                            records TEXT[];
                            inv_rec TEXT[];
                            rec TEXT;
                            v_inv_no TEXT;
                            inv_type TEXT;
                            rel_inv integer;
                            cust_name integer;
                            br_code integer;
                            act_code integer;
                            create_date timestamp without time zone;
                            status TEXT;
                            activated BOOL;
                            move_type TEXT;
                            cust_seq BOOL; 
                            sys_req BOOL;
                            jou_id integer;
                            fixed_disc numeric;
                            move_exist integer;
                            my_date date;
                            curr integer;
                            comp integer;
                            cus_name Text;
                            cust_type TEXT;
                            country integer ;
                            Na TEXT;
                            ta TEXT;
                            pa TEXT ;
                            mycity TEXT;
                            gov TEXT;
                            mystreet TEXT;
                            BUIL TEXT;
                            my_write_date timestamp without time zone;
                            write_user integer;
                            so_ref TEXT;
                            so_desc TEXT;
                            po_ref TEXT;
                            po_desc TEXT;
                            pro_inv_no TEXT;


                            BEGIN
                                SELECT string_to_array(data,'|')INTO records;
                                foreach rec in ARRAy records LOOP
                                    SELECT String_to_array(rec,'~~') INTO inv_rec;
                                    v_inv_no=inv_rec[1];
                                    inv_type=inv_rec[2];
                                    rel_inv=  (select id from account_move where name=inv_rec[3] and state='valid' limit 1) ;
                                    cust_name=(select id from res_partner where name=inv_rec[4] order  by id desc limit 1);
                                    br_code=(select id from inv_branch where code=inv_rec[5]  limit 1);
                                    act_code=(select id from inv_activity_code where code=inv_rec[6] and active =True limit 1);
                                    create_date=inv_rec[7];
                                    fixed_disc=inv_rec[8];
                                    status=inv_rec[9];
                                    activated=inv_rec[10];
                                    move_type=inv_rec[11];
                                    cust_seq=inv_rec[12];
                                    sys_req=inv_rec[13];
                                    jou_id=inv_rec[14];
                                    my_date=inv_rec[15];
                                    curr=inv_rec[16];
                                    comp=inv_rec[17];
                                    my_write_date =inv_rec[18];
                                    write_user =inv_rec[19];
                                    so_ref =inv_rec[20];
                                    so_desc =inv_rec[21];
                                    po_ref =inv_rec[22];
                                    po_desc =inv_rec[23];
                                    pro_inv_no=inv_rec[24];


                                    cus_name=inv_rec[4];
                                    cust_type=(select customer_type from res_partner where id =cust_name);
                                    country =(select country_id from res_partner where id=cust_name);
                                    Na=(select national_id from res_partner where id=cust_name);
                                    ta =(select vat from res_partner where id=cust_name);
                                    pa =(select passport_id from res_partner where id=cust_name);
                                    mycity =(select city from res_partner where id=cust_name);
                                    gov =(select governorate from res_partner where id=cust_name);
                                    mystreet =(select street from res_partner where id=cust_name);
                                    BUIL =(select street2 from res_partner where id=cust_name);


                                    RAISE NOTICE 'i want to print  id: % and type %', cust_name,cust_type;



                                select id from account_move where name=v_inv_no and state='draft' into move_exist ;
                                if move_exist is NULL THEN
                                insert into account_move(name,date,state,move_type,journal_id,partner_id,currency_id,company_id,
                                                         creation_date,invoice_type,
                                                         related_invoice,branch_id,activity_code,invoice_date,invoice_partner_display_name,
                                                        customer_type,country_id,national_id,passport_id,city,governorate,street,street2,tax_id,active,create_date,write_date,create_uid,write_uid,sales_order_reference,sales_order_description,purchase_order_reference,purchase_order_description,proforma_invoice_number,extra_discount) 
                                                         values(v_inv_no,my_date,status,move_type,jou_id,cust_name,
                                curr,comp,create_date,inv_type,rel_inv,br_code,act_code,my_date,cus_name,cust_type,country,Na,pa,mycity,gov,mystreet,BUIL,ta,activated,my_write_date,my_write_date,write_user,write_user,so_ref,so_desc,po_ref,po_desc,pro_inv_no,fixed_disc);

                                END IF;


                                END LOOP;
                            END;

                            $BODY$
                            LANGUAGE plpgsql;


                                """)
