import time

from dtpweb import DTPWeb

def print_text(stock_name,barcode,number):
    '''
    stock_name:  物品名称
    barcode: 商品条码
    number: 打印数量
    '''
    ##初始化打印机
    api = DTPWeb()
    api.check_plugin()

    printers = api.get_printers()
    if len(printers) == 0:
        print("未检测到打印机")
        return None
    label_width = 50    ##标签纸宽度
    label_height = 30   ##标签纸高度
    text_height = 4     ##条形码下面的数字高度
    # 打开打印机
    if api.open_printer(**printers[0]):
        for i in range(number):
            # 创建打印任务，指定标签纸大小。
            api.start_job(label_width, label_height)

            # 绘制字符串
            api.draw_text(stock_name,4,3)       ##物品名称   绘制字符串在标签纸上的x y的位置
            # 绘制一维码，一维码下面的字符串拉伸显示
            api.draw_barcode(barcode, 0, 10, 50,20, text_height)    ##条形码数据   绘制条形码在标签纸上的x y的位置   条形码的高度  条形码下面数字的高度
            # 提交打印任务，开始打印
            api.commit_job()
            time.sleep(2)
    else:
        print("打印机链接失败！")
        return None
    # 关闭打印机
    api.close_printer()
print_text('物品BBBBB物品','1234567890113',20)