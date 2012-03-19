# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

# Date             ID         Message
# 28-12-2011       POP-001    Change rounding accuracy in store procedure round(1/factor)

import math

from osv import fields,osv
import tools
import pooler
from tools.translate import _
from decimal import *
import decimal_precision as dp
import netsvc

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

class ineco_public_function_getstock(osv.osv):
    _name = "ineco.public.function.getstock"
    _description = "Function Get Stock"
    _auto = False
    _columns = {
    }

#POP-001
    def init(self, cr):
        cr.execute("""
            CREATE OR REPLACE FUNCTION ineco_get_stock(integer, double precision)
              RETURNS double precision AS
            $$
              declare 
                uom_id ALIAS FOR $1;
                quantity ALIAS for $2;
                output float;
                uom_ref_id integer;
                refer_qty float;
              begin
                uom_ref_id := (select id from product_uom
                  where category_id = (
                    select category_id from product_uom where id = uom_id) and uom_type = 'reference') ;
                refer_qty = (select
                  case uom_type
                    when 'reference' then quantity * 1
                    when 'bigger' then ineco_round_down(quantity * round(1/factor))
                    when 'smaller' then ineco_round_down(quantity / factor)
                  end
                from
                  product_uom
                where id = uom_id);   
                return refer_qty;
              end;
                
            $$
              LANGUAGE plpgsql 
        """)

ineco_public_function_getstock()

class ineco_public_function_rounddonw(osv.osv):
    _name = "ineco.public.function.rounddonw"
    _description = "Function Rounddown"
    _auto = False
    _columns = {
    }

    def init(self, cr):
        cr.execute("""
            create or replace function ineco_round_down(double precision)
              RETURNS double precision AS
            $BODY$
            declare
              quantity ALIAS FOR $1;
              output float;
              begin
                output = ( select 
                case 
                  when round(quantity) - quantity > 0 then round(quantity)-1
                  else round(quantity)
                end ) ;
                return output;
              end;
            
            $BODY$
            LANGUAGE plpgsql        
        """)
ineco_public_function_rounddonw()


class ineco_public_function_convertstock(osv.osv):
    _name = "ineco.public.function.convertstock"
    _description = "Function Get Stock"
    _auto = False
    _columns = {
    }

#POP-001
    def init(self, cr):
        cr.execute("""
            create or replace function ineco_convert_stock(integer, float) returns float as $$
              declare 
                uom_id ALIAS FOR $1;
                quantity ALIAS for $2;
                output float;
                uom_ref_id integer;
                refer_qty float;
              begin
                uom_ref_id := (select id from product_uom
                  where category_id = (
                    select category_id from product_uom where id = uom_id) and uom_type = 'reference') ;
                if uom_ref_id = uom_id then
                  output = (select
                    case uom_type
                      when 'reference' then quantity * 1
                      --when 'bigger' then ineco_round_down(quantity / factor) 
                      when 'bigger' then ineco_round_down(quantity * round(1/factor)) 
                      when 'smaller' then ineco_round_down(quantity / factor) 
                    end
                  from
                    product_uom
                  where id = uom_id); 
                else
                  refer_qty = (select
                    case uom_type
                      when 'reference' then quantity * 1
                      --when 'bigger' then ineco_round_down(quantity / factor)
                      when 'bigger' then ineco_round_down(quantity * round(1/factor))
                      when 'smaller' then ineco_round_down(quantity / factor) 
                    end
                  from
                    product_uom
                  where id = uom_ref_id); 
                  output = (select
                    case uom_type
                      when 'reference' then refer_qty * 1
                      when 'bigger' then ineco_round_down(refer_qty * factor) 
                      when 'smaller' then ineco_round_down(refer_qty / factor) 
                    end
                  from
                    product_uom
                  where id = uom_id); 
                end if;
                output = (select quantity / round(1/factor) from product_uom where id = uom_id);
                return ineco_round_down(output);
              end;
                
            $$ language 'plpgsql';
        """)

ineco_public_function_convertstock()

class ineco_public_function_getstocklimit(osv.osv):
    _name = "ineco.public.function.getstocklimit"
    _description = "Function Get Stock Limit"
    _auto = False
    _columns = {
    }

#POP-001
    def init(self, cr):
        cr.execute("""
            create or replace function get_stock_limit(int, int) returns int as
            $$
                declare    
                    reccount int default 0;
                    stock record;
                    local_product_id alias for $1;
                    total alias for $2;
                    tmp_quantity int default 0;
            begin
                for stock in select id, qty from tmp_ineco_stock_report where product_id = local_product_id and qty > 0  order by expired, date_input, qty loop
                    tmp_quantity = tmp_quantity + stock.qty;
                    if tmp_quantity >= total then
                        reccount = reccount + 1;
                        exit;
                    end if;
                    reccount = reccount + 1;
                end loop;
                return reccount;
            end;
            $$ language 'plpgsql';
        """)

ineco_public_function_getstocklimit()