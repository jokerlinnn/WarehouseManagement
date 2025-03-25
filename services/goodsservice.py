import db

def get_goods_stock(goods_id):
    # 入库数量
    sql_goods_num_in = '''
    select sum(cast(GOODS_NUM as real)) from STOCK where GOODS_ID = ? and STOCK_TYPE = 1
    '''
    goods_num_in = db.selectone(sql_goods_num_in, (goods_id,))[0] or 0

    # 出库数量
    sql_goods_num_out = '''
    select sum(cast(GOODS_NUM as real)) from STOCK where GOODS_ID = ? and STOCK_TYPE = 0
    '''
    goods_num_out = db.selectone(sql_goods_num_out, (goods_id,))[0] or 0

    return goods_num_in - goods_num_out

def exists(goods_name, barcode, goods_id=-1):
    sql = '''select count(1) from goods where (goods_name = :goods_name or barcode = :barcode) and id != :goods_id'''
    return db.count(sql, (goods_name, barcode, goods_id))

def add_or_update_goods(goods_dict: dict):
    update_sql = '''update goods set goods_name =:goods_name, goods_order=:goods_order, \
        goods_unit=:goods_unit , goods_price=:goods_price, catagory_id=:catagory_id, update_time =:save_time, barcode =:barcode where id =:goods_id'''
    insert_sql = '''insert into goods ( goods_name, goods_order, goods_unit, goods_price , catagory_id, barcode) \
        values( :goods_name ,:goods_order, :goods_unit, :goods_price, :catagory_id, :barcode)'''
    if not  db.update(update_sql, goods_dict):
        db.insert(insert_sql, goods_dict)

def delete_goods(goods_id):
    sql = '''delete from goods where id = ?'''
    return db.delete(sql, (goods_id,))

def get_goods(goods_id):
    sql = '''select a.*, b.catagory_name from goods a , catagory b where a.catagory_id = b.id and a.id = ?'''
    return db.selectone(sql, (goods_id,), return_dict=True)

def get_goods_tree():
    sql = '''select a.catagory_name ,a.id, b.goods_name , b.id from catagory a left join goods b on a.ID = b.catagory_id  order by a.CATAGORY_ORDER desc, b.GOODS_ORDER desc'''
    return db.selectall(sql)

def get_goods_by_barcode(barcode):
    sql = '''select a.*, b.catagory_name from goods a , catagory b where a.catagory_id = b.id and a.barcode LIKE ?'''
    return db.selectall(sql, ('%' + barcode + '%',), return_dict=True)
