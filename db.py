import sqlite3
import logging
import os
import sys
from contextlib import contextmanager
from fractions import Fraction

# 加载日志模块, 开发为了方便调试，可开启debug
logger = logging.getLogger('WarehouseManagement')
#logger.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)
formater = logging.Formatter('%(asctime)-15s [%(levelname)-8s] %(module)s[%(lineno)-4d] %(name)s - %(message)s')
# 输出到文件
consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setLevel(logging.DEBUG)
consoleHandler.setFormatter(formater)
logger.addHandler(consoleHandler)

OP_INSERT = 'insert'
OP_UPDATE = 'update'
OP_DELETE = 'delete'
OP_SELECT = 'select'

try:
    os.mkdir('config')
except:
    pass
_config = {}

# 字典工程，指定sqlite3返回字典形式数据
def dict_factory(cursor, row):
    d = {}
    for index, col in enumerate(cursor.description):
        d[col[0]] = row[index]
    return d

def db_config(database: str, **kw):
    global _config
    kw['database'] = str(database)
    _config = kw


def _get_connection(return_dict=False):
    logger.debug('Fetching JDBC Connection from DataSource [%s] ' % (
        _config['database'],))
    conn = sqlite3.connect(**_config)
    if return_dict:
        conn.row_factory = dict_factory
    logger.debug(
        'Obtained JDBC Connection [%s] for sqlite3 operation' % (conn,))
    return conn


def _close_connection(conn):
    logger.debug('Returning JDBC Connection [%s] to DataSource' % (conn,))
    if conn is not None:
        conn.close()



@contextmanager
def transaction(return_dict=False):
    try:
        conn = _get_connection(return_dict)
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        _close_connection(conn)


def insert(sql, params=None):
    if not sql.lower().strip().startswith(OP_INSERT):
        raise SyntaxError('Not allowed method, specifiy a insert statement.')

    with transaction() as conn:
        cur = conn.cursor()
        logger.debug('Executing Statement: %s' % sql)
        logger.debug('Parameters: %s' % str(params))
        if params:
            if isinstance(params, list):
                cur.executemany(sql, params)
            else:
                cur.execute(sql, params)
        else:
            cur.execute(sql)

        total_changes = conn.total_changes
        logger.debug('Result: %d rows inserted.' % (total_changes,))
        lastid = cur.lastrowid
        
    # 注意一次插入多行时，lastrowid返回None
    return total_changes,lastid


def update(sql, params=None):
    if not sql.lower().strip().startswith(OP_UPDATE):
        raise SyntaxError('Not allowed method, specifiy a update statement.')

    with transaction() as conn:
        cur = conn.cursor()
        logger.debug('Executing Statement: %s' % sql)
        logger.debug('Parameters: %s' % str(params))
        if params:
            cur.execute(sql, params)
        else:
            cur.execute(sql)

        total_changes = conn.total_changes
        logger.debug('Result: %d rows updated.' % (total_changes,))
    return total_changes


def delete(sql, params=None):
    if not sql.lower().strip().startswith(OP_DELETE):
        raise SyntaxError('Not allowed method, specifiy a delete statement.')

    with transaction() as conn:
        cur = conn.cursor()
        logger.debug('Executing Statement: %s' % sql)
        logger.debug('Parameters: %s' % str(params))
        if params:
            cur.execute(sql, params)
        else:
            cur.execute(sql)

        total_changes = conn.total_changes
        logger.debug('Result: %d rows deleted.' % (total_changes,))

    return total_changes


def selectone(sql, params=None, return_dict=False):
    if not sql.lower().strip().startswith(OP_SELECT):
        raise SyntaxError('Not allowed method, specifiy a select statement.')

    with transaction(return_dict) as conn:
        cur = conn.cursor()
        logger.debug('Executing Statement: %s' % sql)
        logger.debug('Parameters: %s' % str(params))
        if params:
            cur.execute(sql, params)
        else:
            cur.execute(sql)

        result = cur.fetchone()
        logger.debug('Result: %s' % (result,))

    return result


def selectall(sql, params=None,return_dict=False):
    if not sql.lower().strip().startswith(OP_SELECT):
        raise SyntaxError('Not allowed method, specifiy a select statement.')

    with transaction(return_dict) as conn:
        cur = conn.cursor()
        logger.debug('Executing Statement: %s' % sql)
        logger.debug('Parameters: %s' % str(params))
        if params:
            cur.execute(sql, params)
        else:
            cur.execute(sql)

        result = cur.fetchall()
        for row in result:
            logger.debug('Result: %s' % (row,))

    return result


def count(sql, params=None):
    row = selectone(sql, params)
    return row[0]


DB_FILE_PATH = 'config/WarehouseManagement.db'
INIT_DB_SCRIPTS = '''
    DROP TABLE IF EXISTS USERS;
    DROP TABLE IF EXISTS CATAGORY;
    DROP TABLE IF EXISTS GOODS;
    DROP TABLE IF EXISTS STOCKS;

CREATE TABLE USERS(
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        USER_NAME VARCHAR(32),
        USER_PASSWORD VARCHAR(64),
        CREATE_TIME DATETIME default (datetime('now', 'localtime')),
        UPDATE_TIME DATETIME
    );

CREATE TABLE [CATAGORY] (
[ID] INTEGER  PRIMARY KEY AUTOINCREMENT NULL,
[CATAGORY_NAME] VARCHAR(64)  NOT NULL,
[CATAGORY_ORDER] INTEGER DEFAULT '1' NOT NULL,
[CATAGORY_DESC] TEXT  NULL,
[CREATE_TIME] DATETIME DEFAULT 'datetime(''now'', ''localtime'')' NULL,
[UPDATE_TIME] DATETIME  NULL
);

CREATE TABLE [GOODS] (
[ID] INTEGER  PRIMARY KEY AUTOINCREMENT NULL,
[GOODS_NAME] VARCHAR(32)  NULL,
[GOODS_PRICE] DECIMAL(11, 2)  NULL,
[GOODS_UNIT] VARCHAR(12)  NULL,
[GOODS_ORDER] INTEGER DEFAULT '1' NOT NULL,
[CATAGORY_ID] INTEGER  NULL,
[CREATE_TIME] DATETIME DEFAULT 'datetime(''now'', ''localtime'')' NULL,
[UPDATE_TIME] DATETIME  NULL
);
   
CREATE TABLE STOCK (
    ID          INTEGER      PRIMARY KEY AUTOINCREMENT,
    STOCK_TYPE  TINYINT      NOT NULL,
    STOCK_DATE  DATE         NOT NULL,
    GOODS_ID    INTEGER      NOT NULL,
    GOODS_NUM   VARCHAR (12)     NOT NULL,
    GOODS_UNIT   VARCHAR (12)      NOT NULL,
    GOODS_PRICE   DECIMAL(11,2)      NOT NULL,
    OP_PERSON   VARCHAR (16),
    OP_AREA     VARCHAR (32),
    CREATE_TIME DATETIME     DEFAULT (datetime('now', 'localtime') ),
    UPDATE_TIME DATETIME,
    FOREIGN KEY (
        GOODS_ID
    )
    REFERENCES GOODS (ID) 
);
    INSERT INTO USERS (user_name, user_password) VALUES ('sysadmin','48a365b4ce1e322a55ae9017f3daf0c0');
    '''

if not os.path.exists(DB_FILE_PATH):
    # 若数据库文件不存在则初始化建库语句
    db_config(DB_FILE_PATH)
    with transaction() as conn:
        conn.executescript(INIT_DB_SCRIPTS)
else:
    db_config(DB_FILE_PATH)

def mod(a, b):
    '''
    :param a: 分子
    :param b: 分母
    :return: 整除，余
    '''
    c = a // b
    r = a - c * b
    return c,r

def jugement(num):
    try:
        return int(num)
    except:
        try:
            float(num)
            return num
        except:
            try:
                f = num.split('/')
                for i in f:
                    int(i)
                return num
            except:
                print('输入的参数有误')
def Get_in_out_price(GOOD_NAME):
    # 1.硬盘上创建连接
    con = sqlite3.connect('config/WarehouseManagement.db')
    # 获取cursor对象
    cur = con.cursor()
    # 执行sql创建表
    sql_id = '''select id from GOODS where GOODS_NAME = '{}'
    '''.format(GOOD_NAME)

    cur.execute(sql_id)
    # 获取所有数据
    id = cur.fetchall()
    # 获取商品id
    goods_id = id[0][0]


    # 入库数量及商品总价
    sql_goods_num_in = '''
    select GOODS_NUM,GOODS_PRICE from STOCK where GOODS_ID = {} and STOCK_TYPE = 1
    '''.format(goods_id)
    cur.execute(sql_goods_num_in)
    _goods_num_in = cur.fetchall()
    # print(_goods_num_in)
    goods_num_in = 0
    Total_price_of_goods = 0
    for i in _goods_num_in:
        num_in = jugement(i[0])
        goods_num_in = Fraction(goods_num_in) + Fraction(num_in)
        Total_price_of_goods = Fraction(Total_price_of_goods) + (Fraction(num_in) *i[1])

    # print(goods_num_in)
    # print(Total_price_of_goods)
    # 入库单价

    # 出库数量
    sql_goods_num_out = '''
    select GOODS_NUM from STOCK where GOODS_ID = {} and STOCK_TYPE = 0
    '''.format(goods_id)
    cur.execute(sql_goods_num_out)
    _goods_num_out = cur.fetchall()
    goods_num_out = 0
    for j in _goods_num_out:
        goods_num_out = Fraction(goods_num_out) + Fraction(jugement(j[0]))
    # print(goods_num_out)
    # 关闭游标
    cur.close()
    # 关闭连接
    con.close()
    return goods_num_in,goods_num_out,Total_price_of_goods
