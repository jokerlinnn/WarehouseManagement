import wx
import time
from wx.lib.mixins.treemixin import ExpansionState
import wx.lib.mixins.listctrl as listmix
import images
import wx.adv
import wx.lib.buttons as buttons
import wx.grid as gridlib
import re
from dtpweb import DTPWeb
import db
import os
from collections import OrderedDict
from ui.catagory import AddorEditCatagoryDialog
from ui.goods import AddorEditGoodsDialog
from services import catagoryservice, goodsservice, stockservice, downloadservice
import model
import winsound
from fractions import Fraction

class GoodsTreeCtrl(ExpansionState, wx.TreeCtrl):
    '''
    继承ExpansionState，表示记录展开状态的树状控件
    '''
    def __init__(self, parent):
        wx.TreeCtrl.__init__(self, parent, style=wx.TR_DEFAULT_STYLE | 
                             wx.TR_HAS_VARIABLE_ROW_HEIGHT)
        self.BuildTreeImageList()
        self.SetInitialSize((100, 80))

    def BuildTreeImageList(self):
        '''
        初始化树状控件图标
        '''
        imgList = wx.ImageList(16, 16)
        for png in images.catalog.values():
            imgList.Add(png.GetBitmap())

        self.AssignImageList(imgList)

# 打印函数
def print_function(stock_name,barcode,number):
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
        wx.MessageBox("未检测到打印机,请检查USB线是否正确连接,驱动是否正确安装", "错误", wx.OK | wx.ICON_ERROR)
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
        wx.MessageBox("打印机链接失败,请检查USB线是否正确连接,驱动是否正确安装", "错误", wx.OK | wx.ICON_ERROR)
        return None
    # 关闭打印机
    api.close_printer()

class PrintDialog(wx.Dialog):
    def __init__(self, parent, goods_name, barcode):
        super().__init__(parent, title="打印条形码")

        panel = wx.Panel(self)

        # 创建静态文本和文本框
        goods_name_label = wx.StaticText(panel, label="物品名称:")
        self.goods_name_text = wx.TextCtrl(panel, value=goods_name, style=wx.TE_READONLY)

        barcode_label = wx.StaticText(panel, label="物品条形码:")
        self.barcode_text = wx.TextCtrl(panel, value=barcode, style=wx.TE_READONLY)

        print_count_label = wx.StaticText(panel, label="打印数量:")
        self.print_count_text = wx.TextCtrl(panel)

        # 创建打印按钮
        print_button = wx.Button(panel, label="打印")
        print_button.Bind(wx.EVT_BUTTON, self.on_print)

        # 创建布局
        sizer = wx.BoxSizer(wx.VERTICAL)
        grid_sizer = wx.FlexGridSizer(3, 2, 5, 5)
        grid_sizer.Add(goods_name_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.goods_name_text, 0, wx.EXPAND)
        grid_sizer.Add(barcode_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.barcode_text, 0, wx.EXPAND)
        grid_sizer.Add(print_count_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.print_count_text, 0, wx.EXPAND)

        sizer.Add(grid_sizer, 0, wx.ALL | wx.EXPAND, 10)
        sizer.Add(print_button, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)

        panel.SetSizer(sizer)
        sizer.Fit(self)

    def on_print(self, event):
        goods_name = self.goods_name_text.GetValue()
        barcode = self.barcode_text.GetValue()
        print_count = self.print_count_text.GetValue()

        if print_count.isdigit():
            print_function(goods_name, barcode, int(print_count))
            self.Close()
        else:
            wx.MessageBox("打印数量必须为数字", "错误", wx.OK | wx.ICON_ERROR)


class GoodsTreeCtrlPanel(wx.Panel):
    '''
    左侧物品树状控件、查询控件面板
    '''
    def __init__(self, parent):
        super(GoodsTreeCtrlPanel, self).__init__(
            parent, style=wx.TAB_TRAVERSAL | wx.CLIP_CHILDREN)

        self.filter = wx.SearchCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.filter.ShowCancelButton(True)
        self.filter.Bind(wx.EVT_TEXT, self.RecreateTree)
        self.filter.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN,
                         lambda e: self.filter.SetValue(''))

        searchMenu = wx.Menu()
        name_search = searchMenu.AppendRadioItem(-1, "物品名称")
        barcode_search = searchMenu.AppendRadioItem(-1, "条码")
        # 设置条码查询为默认选中
        searchMenu.Check(name_search.GetId(), True)

        self.filter.SetMenu(searchMenu)
        self.filter.Bind(wx.EVT_MENU, self.OnSearchMenuSelect)

        # # 新增条形码搜索框
        # self.barcode_filter = wx.SearchCtrl(self, style=wx.TE_PROCESS_ENTER)
        # self.barcode_filter.ShowCancelButton(True)
        # self.barcode_filter.Bind(wx.EVT_TEXT, self.RecreateTreeByBarcode)
        # self.barcode_filter.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN,
        #                          lambda e: self.barcode_filter.SetValue(''))

        self.tree = GoodsTreeCtrl(self)
        self.tree.SetExpansionState([0, 1])
        self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelChanged)
        self.tree.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        self.tree.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)

        leftBox = wx.BoxSizer(wx.VERTICAL)
        leftBox.Add(self.tree, 1, wx.EXPAND)
        leftBox.Add(wx.StaticText(self, label="查询条件:"), 0, wx.TOP | wx.LEFT, 5)
        leftBox.Add(self.filter, 0, wx.EXPAND | wx.ALL, 5)
        # leftBox.Add(self.barcode_filter, 0, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(leftBox) 

        # 当前选中的物品
        self.currentItem = None
        self.current_search_type = 0
        # 加载数据库物品信息
        self.goods_data = self.queryGoodsData()
        self.RecreateTree()

        model.goodsListModel.addListener(self.OnUpdate)

    def OnSearchMenuSelect(self, event):
        item = event.GetEventObject().FindItemById(event.GetId())
        if item.GetText() == "物品名称":
            self.current_search_type = 0
        elif item.GetText() == "条码":
            self.current_search_type = 1
        self.RecreateTree()

    def queryGoodsData(self):
        goodsTree = goodsservice.get_goods_tree() 
        goods_data = OrderedDict()
        for row in goodsTree:
            catagory_name, catagory_id, goods_name, goods_id = row
            if (catagory_name, catagory_id )not in goods_data:
                if goods_name is None:
                    goods_data[catagory_name, catagory_id] = []
                else:
                    goods_data[catagory_name, catagory_id] = [(goods_name, goods_id)]
            else: 
                goods_data[catagory_name, catagory_id].append((goods_name, goods_id))
        
        return goods_data

    # ---------------------------------------------
    def OnSelChanged(self, event):
        try:
            wx.BeginBusyCursor()
            #self.GetParent().Freeze()
            item = event.GetItem()
            self.currentItem = item

            itemData = self.tree.GetItemData(item)
            #catagory_id, goods_id = itemData
            goods_id = itemData[1]
            if goods_id is None:
                return

            goodsinfo = goodsservice.get_goods(goods_id)
            model.goodsDeatilModel.set(goodsinfo)


        finally:
            wx.EndBusyCursor()
            #self.GetParent().Thaw()


    def RecreateTree(self, evt=None, current=None):
        expansionState = self.tree.GetExpansionState()

        self.tree.Freeze()
        self.tree.DeleteAllItems()
        self.root = self.tree.AddRoot("物品概览")
        self.tree.SetItemImage(self.root, 0)
        self.tree.SetItemData(self.root, (-1, None))

        treeFont = self.tree.GetFont()
        catFont = self.tree.GetFont()

        treeFont.SetWeight(wx.FONTWEIGHT_BOLD)
        catFont.SetWeight(wx.FONTWEIGHT_BOLD)
        self.tree.SetItemFont(self.root, treeFont)

        # 第一个子节点
        firstChild = None
        # 当前选中的节点
        selectedItem = None
        if current is None and self.currentItem is not None:
            current = self.tree.GetItemText(self.currentItem)
        # 过滤条件
        filterValue = self.filter.GetValue()
        count = 0
        all_matched_goods = []  # 用于存储所有匹配的物品信息

        if self.current_search_type == 0:  # 物品名称查询
            filterValue = self.filter.GetValue()
            if filterValue:
                # 用于存储包含搜索物品的类别
                valid_categories = {}
                for category, items in self.goods_data.items():
                    filtered_items = [item for item in items if filterValue.lower() in item[0].lower()]
                    if filtered_items:
                        valid_categories[category] = filtered_items

                for category, items in valid_categories.items():
                    catagory_name, catagory_id = category
                    count += 1
                    child = self.tree.AppendItem(self.root, catagory_name, image=count)
                    self.tree.SetItemFont(child, catFont)
                    self.tree.SetItemData(child, (catagory_id, None))

                    if current and current == catagory_name:
                        selectedItem = child

                    if not firstChild:
                        firstChild = child

                    for childItem in items:
                        image = count % len(images.catalog)
                        goods_name, goods_id = childItem
                        goodsItem = self.tree.AppendItem(child, goods_name, image=image)
                        self.tree.SetItemData(goodsItem, (catagory_id, goods_id))
                        all_matched_goods.append((goods_name, goods_id))  # 存储匹配的物品信息

                        if current and current == goods_name:
                            selectedItem = goodsItem
            else:
                # 没有输入搜索值，显示所有物品
                for category, items in self.goods_data.items():
                    catagory_name, catagory_id = category
                    count += 1
                    child = self.tree.AppendItem(self.root, catagory_name, image=count)
                    self.tree.SetItemFont(child, catFont)
                    self.tree.SetItemData(child, (catagory_id, None))

                    if current and current == catagory_name:
                        selectedItem = child

                    if not firstChild:
                        firstChild = child

                    for childItem in items:
                        image = count % len(images.catalog)
                        goods_name, goods_id = childItem
                        goodsItem = self.tree.AppendItem(child, goods_name, image=image)
                        self.tree.SetItemData(goodsItem, (catagory_id, goods_id))
                        all_matched_goods.append((goods_name, goods_id))  # 存储匹配的物品信息

                        if current and current == goods_name:
                            selectedItem = goodsItem
        elif self.current_search_type == 1:  # 条码查询
            filterValue = self.filter.GetValue()
            if filterValue:
                goods_infos = goodsservice.get_goods_by_barcode(filterValue)
                for goods_info in goods_infos:
                    catagory_name = goods_info['CATAGORY_NAME']
                    catagory_id = goods_info['CATAGORY_ID']
                    goods_name = goods_info['GOODS_NAME']
                    goods_id = goods_info['ID']

                    # 检查类别节点是否已存在
                    category_item = None
                    child, cookie = self.tree.GetFirstChild(self.root)
                    while child.IsOk():
                        if self.tree.GetItemText(child) == catagory_name:
                            category_item = child
                            break
                        child = self.tree.GetNextSibling(child)

                    if not category_item:
                        category_item = self.tree.AppendItem(self.root, catagory_name, image=1)
                        self.tree.SetItemFont(category_item, catFont)
                        self.tree.SetItemData(category_item, (catagory_id, None))

                    goodsItem = self.tree.AppendItem(category_item, goods_name, image=0)
                    self.tree.SetItemData(goodsItem, (catagory_id, goods_id))
                    all_matched_goods.append((goods_name, goods_id))  # 存储匹配的物品信息

                    if current and current == goods_name:
                        selectedItem = goodsItem
            else:
                # 条码输入框为空，展示所有物品
                count = 0
                for category, items in self.goods_data.items():
                    catagory_name, catagory_id = category
                    count += 1
                    child = self.tree.AppendItem(self.root, catagory_name, image=count)
                    self.tree.SetItemFont(child, catFont)
                    self.tree.SetItemData(child, (catagory_id, None))

                    if not firstChild:
                        firstChild = child

                    for childItem in items:
                        image = count % len(images.catalog)
                        goods_name, goods_id = childItem
                        goodsItem = self.tree.AppendItem(child, goods_name, image=image)
                        self.tree.SetItemData(goodsItem, (catagory_id, goods_id))
                        all_matched_goods.append((goods_name, goods_id))  # 存储匹配的物品信息

        self.tree.Expand(self.root)
        if selectedItem is None and firstChild:
            self.tree.Expand(firstChild)
        if filterValue:
            self.tree.ExpandAll()
        elif expansionState:
            self.tree.SetExpansionState(expansionState)
        if selectedItem:
            self.tree.SelectItem(selectedItem)

        # 根据匹配的物品数量展示相应的物品信息
        if all_matched_goods:
            if len(all_matched_goods) == 1:
                # 查询结果只有一件物品
                _, goods_id = all_matched_goods[0]
            else:
                # 查询结果有多件物品，选择第一件
                _, goods_id = all_matched_goods[0]
            goodsinfo = goodsservice.get_goods(goods_id)
            model.goodsDeatilModel.set(goodsinfo)

        self.tree.Thaw()
    def OnUpdate(self, m):
        self.goods_data = self.queryGoodsData()
        self.RecreateTree(current=m.current)

    def OnRightDown(self,evt):
        pt = evt.GetPosition()
        #item, flags = self.tree.HitTest(pt)
        item = self.tree.HitTest(pt)[0]
        if item:
            self.tree.SelectItem(item)
            self.currentItem = item

    def OnRightUp(self,evt):
        pt = evt.GetPosition()
        #item, flags = self.tree.HitTest(pt)
        item = self.tree.HitTest(pt)[0]
        if item:
            # 判断是否是root节点
            if self.tree.GetItemData(item)[0] != -1:
                menu = wx.Menu()
                item1 = menu.Append(wx.ID_ANY, "编辑")
                item2 = menu.Append(wx.ID_ANY, "删除")
                item3 = menu.Append(wx.ID_ANY, "打印")
                self.Bind(wx.EVT_MENU, self.OnItemEdit, item1)
                self.Bind(wx.EVT_MENU, self.OnItemDelete, item2)
                self.Bind(wx.EVT_MENU, self.OnItemPrint, item3)
                # 禁止删除非空的物品类别节点
                childrencount = self.tree.GetChildrenCount(item, recursively=True)
                if childrencount > 0:
                    menu.Enable(item2.GetId(), False)
                self.PopupMenu(menu)
                menu.Destroy()

    def OnItemEdit(self,evt):
        item = self.currentItem
        catagory_id, goods_id = self.tree.GetItemData(item)
        if goods_id is None:
            # 说明选择的为物品类别
            dlg = AddorEditCatagoryDialog(self.Parent.Parent, wx.ID_ANY, "修改物品类别")
            dlg.InitCtrlValue(catagory_id)
            dlg.CenterOnParent(dir=wx.BOTH)
            dlg.ShowModal()
        else:
            dlg = AddorEditGoodsDialog(self.Parent.Parent, '添加物品')
            dlg.InitCtrlValue(goods_id)
            dlg.CenterOnParent(dir=wx.BOTH)
            dlg.ShowModal()

    def OnItemPrint(self, evt):
        # 获取物品名称和条形码
        item = self.currentItem
        catagory_id, goods_id = self.tree.GetItemData(item)
        if goods_id is not None:
            goods = goodsservice.get_goods(goods_id)
            goods_name = goods.get('GOODS_NAME', '')
            barcode = goods.get('BARCODE', '')

            # 弹出打印对话框
            dlg = PrintDialog(self, goods_name, barcode)
            dlg.ShowModal()
            dlg.Destroy()
        else:
            wx.MessageBox("请选择具体的物品", "提示", wx.OK | wx.ICON_INFORMATION)


    def OnItemDelete(self,evt):
        strs = "确定要删除[" + self.tree.GetItemText(self.currentItem) + "]吗?删除后将不可恢复"
        dlg = wx.MessageDialog(None, strs, '温馨提示', wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_QUESTION)

        if dlg.ShowModal() in [wx.ID_NO, wx.ID_CANCEL]:
            dlg.Destroy()
            return
        dlg.Destroy()

        item = self.currentItem
        catagory_id, goods_id = self.tree.GetItemData(item)
        if goods_id is None:
            # 说明选择的为物品类别
            catagoryservice.delete_catagory(catagory_id)
        else:
            goodsservice.delete_goods(goods_id)

        self.tree.DeleteChildren(self.currentItem)
        self.tree.Delete(self.currentItem)
        self.currentItem = None
        self.goods_data = self.queryGoodsData()
###################################


class StockRegisterPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self,parent, -1, style=wx.CLIP_CHILDREN)
        
        # 计算日期选择控件的范围
        now = wx.DateTime.Today()
        beginDate = now.Subtract(wx.DateSpan(months=6))

        labelfont = wx.Font(wx.NORMAL_FONT.GetPointSize(
        ), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        bs1 = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, wx.ID_ANY, '信息登记')
        label.SetFont(labelfont)
        bs1.Add(label, 0, wx.ALL | wx.BOTTOM, 0)

        gbSizer = wx.GridBagSizer(7, 6)
        label = wx.StaticText(self, wx.ID_ANY, '名称：')
        self.tc_goodsname = wx.TextCtrl(
            self, wx.ID_ANY, '', style=wx.TE_READONLY)
        gbSizer.Add(label, (0, 0), (1, 1), wx.ALL | wx.ALIGN_RIGHT,  5)
        gbSizer.Add(self.tc_goodsname, (0, 1), (1, 1),  wx.ALL | wx.EXPAND, 5)


        label = wx.StaticText(self, wx.ID_ANY, '物品数量：')
        # self.tc_goodsNum = IntCtrl(self)
        # self.tc_goodsNum.SetMin(1)
        # self.tc_goodsNum.SetNoneAllowed(True)
        # self.tc_goodsNum.SetValue(None)
        self.tc_goodsNum = wx.TextCtrl(self, wx.ID_ANY, '',style=wx.TE_READONLY)
        self.tc_goodsNum.SetMaxLength(12)
        gbSizer.Add(label, (0, 2), (1, 1),  wx.ALL | wx.ALIGN_RIGHT,  5)
        gbSizer.Add(self.tc_goodsNum, (0, 3), (1, 1), wx.ALL | wx.EXPAND, 5)

        label = wx.StaticText(self, wx.ID_ANY, '类别：')
        self.tc_goodcatagory = wx.TextCtrl(
            self, wx.ID_ANY, '', style=wx.TE_READONLY)
        gbSizer.Add(label, (1, 0), (1, 1), wx.ALL,  5)
        gbSizer.Add(self.tc_goodcatagory, (1, 1),
                    (1, 1),  wx.ALL | wx.EXPAND, 5)

        label = wx.StaticText(self, wx.ID_ANY, '经办人员：')
        self.tc_op = wx.TextCtrl(self, wx.ID_ANY, '')
        self.tc_op.SetMaxLength(10)
        gbSizer.Add(label, (3, 2), (1, 1), wx.ALL | wx.ALIGN_RIGHT, 5)
        gbSizer.Add(self.tc_op, (3, 3), (1, 1), wx.ALL | wx.EXPAND, 5)

        label = wx.StaticText(self, wx.ID_ANY, '规格：')
        self.tc_goodsunit = wx.TextCtrl(
            self, wx.ID_ANY, '',style=wx.TE_READONLY)
        self.tc_goodsunit.SetMaxLength(6)
        gbSizer.Add(label, (4, 0), (1, 1), wx.ALL | wx.ALIGN_RIGHT, 5)
        gbSizer.Add(self.tc_goodsunit, (4, 1), (1, 1), wx.ALL | wx.EXPAND, 5)

        label = wx.StaticText(self, wx.ID_ANY, '经办地点：')
        self.tc_address = wx.TextCtrl(self, wx.ID_ANY, '',style=wx.TE_READONLY)
        self.tc_address.SetMaxLength(24)
        gbSizer.Add(label, (4, 2), (1, 1), wx.ALL | wx.ALIGN_RIGHT, 5)
        gbSizer.Add(self.tc_address, (4, 3), (1, 1), wx.ALL | wx.EXPAND, 5)

        label = wx.StaticText(self, wx.ID_ANY, '物品单价：')
        self.tc_goodsprice = wx.TextCtrl(self, wx.ID_ANY, '', style=wx.TE_READONLY)
        self.tc_goodsprice.SetMaxLength(12)
        self.tc_goodsprice.Bind(wx.EVT_CHAR, self.OnFloatChar)
        gbSizer.Add(label, (1, 2), (1, 1), wx.ALL, 5)
        gbSizer.Add(self.tc_goodsprice, (1, 3), (1, 1), wx.ALL | wx.EXPAND, 5)

        label = wx.StaticText(self, wx.ID_ANY, '登记日期：')
        self.op_date = wx.adv.DatePickerCtrl(self, size=(120, -1),
                                             style=wx.adv.DP_DROPDOWN
                                                   | wx.adv.DP_SHOWCENTURY)
        # self.Bind(wx.adv.EVT_DATE_CHANGED, self.OnDateChanged, self.op_date)
        self.op_date.SetRange(beginDate, wx.DateTime.Today())
        gbSizer.Add(label, (5, 2), (1, 1), wx.ALL | wx.ALIGN_RIGHT, 5)
        gbSizer.Add(self.op_date, (5, 3), (1, 1), wx.ALL | wx.EXPAND, 5)

        label = wx.StaticText(self, wx.ID_ANY, '当前合计：')
        self.tc_totalamount = wx.TextCtrl(
            self, wx.ID_ANY, '', style=wx.TE_READONLY)
        gbSizer.Add(label, (2, 2), (1, 1), wx.ALL | wx.ALIGN_RIGHT, 5)
        gbSizer.Add(self.tc_totalamount, (2, 3), (1, 1), wx.ALL | wx.EXPAND, 5)


        label = wx.StaticText(self, wx.ID_ANY, '库存：')
        self.tc_currentinventory = wx.TextCtrl(
            self, wx.ID_ANY, '', style=wx.TE_READONLY)
        gbSizer.Add(label, (2, 0), (1, 1), wx.ALL | wx.ALIGN_RIGHT, 5)
        gbSizer.Add(self.tc_currentinventory, (2, 1), (1, 1), wx.ALL | wx.EXPAND, 5)

        label = wx.StaticText(self, wx.ID_ANY, '总计：')
        self.tc_totalamounts = wx.TextCtrl(
            self, wx.ID_ANY, '', style=wx.TE_READONLY)
        gbSizer.Add(label, (5, 0), (1, 1), wx.ALL | wx.ALIGN_RIGHT, 5)
        gbSizer.Add(self.tc_totalamounts, (5, 1), (1, 1), wx.ALL | wx.EXPAND, 5)

        label = wx.StaticText(self, wx.ID_ANY, '总值：')
        self.tc_now_totalamounts = wx.TextCtrl(
            self, wx.ID_ANY, '', style=wx.TE_READONLY)
        gbSizer.Add(label, (3, 0), (1, 1), wx.ALL | wx.ALIGN_RIGHT, 5)
        gbSizer.Add(self.tc_now_totalamounts, (3, 1), (1, 1), wx.ALL | wx.EXPAND, 5)

        # 新增条码元素
        label = wx.StaticText(self, wx.ID_ANY, '条码：')
        self.tc_barcode = wx.TextCtrl(
            self, wx.ID_ANY, '', style=wx.TE_READONLY)
        gbSizer.Add(label, (6, 0), (1, 1), wx.ALL | wx.ALIGN_RIGHT, 5)
        gbSizer.Add(self.tc_barcode, (6, 1), (1, 1), wx.ALL | wx.EXPAND, 5)


        gbSizer.AddGrowableCol(1)
        gbSizer.AddGrowableCol(3)

        bs2 = wx.BoxSizer(wx.HORIZONTAL)
        bs2.AddStretchSpacer(1)
        b = buttons.GenButton(self, -1, "入库")
        self.Bind(wx.EVT_BUTTON, self.OnInStock, b)
        bs2.Add(b, 0, wx.ALL, 5)
        b = buttons.GenButton(self, -1, "出库")
        self.Bind(wx.EVT_BUTTON, self.OnOutStock, b)
        bs2.Add(b, 0, wx.ALL, 5)
        # b = buttons.GenButton(self, -1, "重置")
        # self.Bind(wx.EVT_BUTTON, self.OnReset, b)
        # bs2.Add(b, 0, wx.ALL, 5)
        # b = buttons.GenButton(self, -1, "计算合计")
        # self.Bind(wx.EVT_BUTTON, self.OnCalculate, b)
        # bs2.Add(b, 0, wx.ALL, 5)
        bs2.AddStretchSpacer(1)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(bs1, 0, wx.ALL, 5)
        line = wx.StaticLine(self, -1, size=(20, -1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL |
                  wx.RIGHT | wx.TOP, 0)
        sizer.Add(gbSizer, 0, wx.ALL | wx.EXPAND, 5)
        sizer.Add(bs2, 0, wx.ALL | wx.EXPAND, 0)

        bs3 = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, wx.ID_ANY, '出入库记录')
        label.SetFont(labelfont)
        bs3.Add(label, 0, wx.ALL, 0)

        sizer.Add(bs3, 0, wx.ALL, 5)
        line1 = wx.StaticLine(self, -1, size=(20, -1), style=wx.LI_HORIZONTAL)
        sizer.Add(line1, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL |
                  wx.RIGHT | wx.TOP, 0)
        
        bs4 = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, wx.ID_ANY, '物品名称：')
        self.s_goodsname = wx.TextCtrl(self, wx.ID_ANY, size=(120,-1), style=wx.TE_PROCESS_ENTER)
        self.s_goodsname.SetMaxLength(16)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnTextEnter, self.s_goodsname)
        
        bs4.Add(label, 0, wx.ALL | wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL,  5)
        bs4.Add(self.s_goodsname,0, wx.ALL | wx.EXPAND, 5)
        
        label = wx.StaticText(self, wx.ID_ANY, '登记日期：')
        self.registerDate = wx.adv.DatePickerCtrl(self, size=(120,-1), style=wx.adv.DP_DROPDOWN| wx.adv.DP_SHOWCENTURY)
        self.registerDate.SetRange(wx.DateTime.Today().Subtract(wx.DateSpan(months=6)), wx.DateTime.Today())
        self.Bind(wx.adv.EVT_DATE_CHANGED, self.OnDateChanged, self.registerDate)
        
        bs4.Add(label, 0, wx.ALL | wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL,  5)
        bs4.Add(self.registerDate, 0, wx.ALL | wx.EXPAND, 5)
        cBtn = wx.ContextHelpButton(self)
        cBtn.SetHelpText("默认显示当天登记的记录，并且可以对记录进行删除和修改操作。")
        bs4.Add(cBtn, 0, wx.ALL | wx.EXPAND, 5)

        bs5 = wx.BoxSizer(wx.VERTICAL)
        self.list = SockListCtrl(self, -1, style=wx.LC_REPORT | wx.LC_SINGLE_SEL| wx.BORDER_NONE| wx.LC_HRULES | wx.LC_VRULES)
        self.list.Bind(wx.EVT_COMMAND_RIGHT_CLICK, self.OnRightClick)
        #self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated, self.list)
        #self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected, self.list)

        bs5.Add(self.list, 1, wx.ALL | wx.EXPAND, 5)

        sizer.Add(bs4, 0, wx.ALL | wx.EXPAND, 5)
        sizer.Add(bs5, 1, wx.ALL|wx.EXPAND, 5)
        self.SetSizer(sizer)

        
        self.goodsId = None
        self.currentItem = None



        model.goodsDeatilModel.addListener(self.OnUpdate)
        self.queryStocksByDate()




    def queryStocksByDate(self):
        registerDate = self.registerDate.GetValue().Format('%Y-%m-%d')
        goodsName = self.s_goodsname.GetValue().strip()
        result = stockservice.get_stocks({
                'goods_name': goodsName,
                'startdate': registerDate
            })
        self.setData(result)
    
    def OnDateChanged(self, evt):
        self.queryStocksByDate()
        
    def OnTextEnter(self,evt):
        self.queryStocksByDate()
        
    def OnRightClick(self, evt):
        # 只第一次绑定事件
        if not hasattr(self, "removeId"):
            self.removeId = wx.NewIdRef()
            self.editId = wx.NewIdRef()

            self.Bind(wx.EVT_MENU, self.OnDelete, id=self.removeId)
            #self.Bind(wx.EVT_MENU, self.OnEdit, id=self.editId)
           
        menu = wx.Menu()
        menu.Append(self.removeId, "删除")
        #menu.Append(self.editId, "编辑")
        self.PopupMenu(menu)
        menu.Destroy()
    

    def OnUpdate(self, m):
        self.tc_goodsname.SetValue(m.data['GOODS_NAME'])
        self.tc_goodsunit.SetValue(m.data['GOODS_UNIT'])
        self.tc_goodsprice.SetValue(str(m.data['GOODS_PRICE']))
        self.tc_goodcatagory.SetValue(m.data['CATAGORY_NAME'])
        self.tc_barcode.SetValue(m.data.get('BARCODE', ''))
        self.goodsId = m.data['ID']
        goods_num_in, goods_num_out, Total_price_of_goods = db.Get_in_out_price(self.tc_goodsname.GetValue())
        self.currentinventory = goods_num_in-goods_num_out
        if self.currentinventory.denominator == 1:
            self.tc_currentinventory.SetValue(str(self.currentinventory))
            self.tc_totalamounts.SetValue(str(round(Total_price_of_goods, 2)))
        else:
            currentinventory = str(int(self.currentinventory)) + ' +'+str(self.currentinventory.numerator -
                                             int(self.currentinventory) *self.currentinventory.denominator)  + '/' +\
                               str(self.currentinventory.denominator)
            self.tc_currentinventory.SetValue(currentinventory)

        now_totalamounts = self.currentinventory * float(self.tc_goodsprice.GetValue())
        self.tc_now_totalamounts.SetValue(str(round(now_totalamounts, 2)))

    def OnInStock0(self, evt):
        self.SaveStock(1)

    def OnConfirmOutStock(self, event):
        # 遍历out_stock_items执行出库
        for barcode, (index, goods_name, current_stock, reduce_stock) in self.out_stock_items.items():
            # 获取物品ID（需从goods_info中获取）
            goods_info = goodsservice.get_goods_by_barcode_exact(barcode)[0]
            goods_id = goods_info['ID']
            stock_date = wx.DateTime.Today().Format('%Y-%m-%d')

            # 出库参数（stock_type需根据业务逻辑设置，如0表示出库）
            params = {
                'STOCK_TYPE': 0,
                'STOCK_DATE': stock_date,
                'GOODS_ID': goods_id,
                'GOODS_NUM': str(reduce_stock),  # 减少的数量
                'GOODS_UNIT': goods_info['GOODS_UNIT'],
                'GOODS_PRICE': goods_info['GOODS_PRICE'],
                'OP_PERSON': self.tc_op.GetValue(),  # 可从界面获取操作人
                'OP_AREA': self.tc_address.GetValue()  # 可从界面获取地点
            }

            # 执行出库操作
            stockservice.add_stock(params)


        # 关闭对话框并刷新库存显示
        event.GetEventObject().GetTopLevelParent().Close()
        self.queryStocksByDate()

        wx.MessageBox('更新库存成功', '温馨提示', wx.YES_DEFAULT | wx.ICON_EXCLAMATION)


    def OnConfirmInStock(self, event):
        # 遍历in_stock_items执行入库
        for barcode, (index, goods_name, price, in_stock_num) in self.in_stock_items.items():
            # 获取物品ID
            goods_info = goodsservice.get_goods_by_barcode_exact(barcode)[0]
            goods_id = goods_info['ID']
            stock_date = wx.DateTime.Today().Format('%Y-%m-%d')

            # 入库参数（stock_type=1表示入库）
            params = {
                'STOCK_TYPE': 1,
                'STOCK_DATE': stock_date,
                'GOODS_ID': goods_id,
                'GOODS_NUM': str(in_stock_num),
                'GOODS_UNIT': goods_info['GOODS_UNIT'],
                'GOODS_PRICE': str(price),
                'OP_PERSON': self.tc_op.GetValue(),
                'OP_AREA': self.tc_address.GetValue()
            }

            stockservice.add_stock(params)  # 执行入库操作

        event.GetEventObject().GetTopLevelParent().Close()
        self.queryStocksByDate()
        wx.MessageBox('入库操作完成', '温馨提示', wx.YES_DEFAULT | wx.ICON_EXCLAMATION)

    def OnInStock(self, evt):
        self.in_stock_items = {}  # 存储入库物品信息

        dlg = wx.Dialog(self, title="入库操作", size=(530, 300))
        sizer = wx.BoxSizer(wx.VERTICAL)

        # 定义on_query函数（需在控件创建前定义）
        def on_query(evt):
            barcode = barcode_input.GetValue().strip()

            if not barcode:
                wx.MessageBox('请输入条形码!', '温馨提示', wx.YES_DEFAULT | wx.ICON_EXCLAMATION)
                return

            try:
                goods_num = Fraction(1)  # 默认入库数量为1
            except:
                wx.MessageBox('数量格式错误', '错误', wx.OK)
                return

            goods_info_list = goodsservice.get_goods_by_barcode_exact(barcode)
            if not goods_info_list:
                winsound.Beep(2000, 800)
                wx.MessageBox('未找到该条形码', '提示', wx.OK)
                return

            goods_info = goods_info_list[0]
            goods_name = goods_info['GOODS_NAME']
            goods_id = goods_info['ID']
            current_stock = goodsservice.get_goods_stock(goods_id)


            if barcode in self.in_stock_items:
                idx, _, current_stock, in_stock_num = self.in_stock_items[barcode]
                new_in_stock = in_stock_num + goods_num
                list_ctrl.SetItem(idx, 3, str(new_in_stock))
                self.in_stock_items[barcode] = (idx, goods_name, current_stock, new_in_stock)
            else:
                idx = list_ctrl.InsertItem(list_ctrl.GetItemCount(), goods_name)
                list_ctrl.SetItem(idx, 1, barcode)
                list_ctrl.SetItem(idx, 2, str(current_stock))  # 当前库存
                list_ctrl.SetItem(idx, 3, str(goods_num))
                self.in_stock_items[barcode] = (idx, goods_name, goods_info.get('GOODS_PRICE', 0), goods_num)

            #扫码成功提示音
            winsound.MessageBeep(winsound.MB_OK)

            barcode_input.SetValue("")  # 清空输入框

        # 创建条形码输入框并绑定事件
        barcode_label = wx.StaticText(dlg, label="条形码：")
        barcode_input = wx.SearchCtrl(dlg, style=wx.TE_PROCESS_ENTER)
        barcode_input.Bind(wx.EVT_TEXT_ENTER, on_query)

        input_sizer = wx.BoxSizer(wx.HORIZONTAL)
        input_sizer.Add(barcode_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        input_sizer.Add(barcode_input, 1, wx.ALL | wx.EXPAND, 5)
        sizer.Add(input_sizer, 0, wx.ALL | wx.EXPAND, 5)

        # 创建确认按钮

        query_button = wx.Button(dlg, label="查询")
        confirm_button = wx.Button(dlg, label="确定执行入库")  # 新增确定按钮

        # 调整布局，将查询和确定按钮放在同一行
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(query_button, 0, wx.ALL, 5)
        button_sizer.Add(confirm_button, 0, wx.ALL, 5)
        sizer.Add(button_sizer, 0, wx.ALL | wx.ALIGN_CENTER, 5)  # 替换原单独添加的query_button

        confirm_button.Bind(wx.EVT_BUTTON, self.OnConfirmInStock)  # 绑定确认事件

        barcode_input.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, on_query)  # 绑定搜索按钮事件
        barcode_input.Bind(wx.EVT_TEXT_ENTER, on_query)  # 绑定回车键事件

        query_button.Bind(wx.EVT_BUTTON, on_query)


        # 创建列表控件
        list_ctrl = wx.ListCtrl(dlg, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_NONE | wx.LC_HRULES | wx.LC_VRULES)
        list_ctrl.InsertColumn(0, "物品名称")
        list_ctrl.InsertColumn(1, "条形码")
        list_ctrl.InsertColumn(2, "当前库存")
        list_ctrl.InsertColumn(3, "入库数量")
        list_ctrl.SetColumnWidth(0, 150)
        list_ctrl.SetColumnWidth(1, 150)
        list_ctrl.SetColumnWidth(2, 100)
        list_ctrl.SetColumnWidth(3, 100)
        sizer.Add(list_ctrl, 1, wx.ALL | wx.EXPAND, 5)

        dlg.SetSizer(sizer)
        dlg.CenterOnParent()
        dlg.ShowModal()
        dlg.Destroy()

    def OnOutStock(self, evt):

        self.out_stock_items = {}  # 用于存储出库物品信息

        # 创建二级页面
        dlg = wx.Dialog(self, title="出库操作", size=(530, 300))
        sizer = wx.BoxSizer(wx.VERTICAL)

        # 条形码输入框
        barcode_label = wx.StaticText(dlg, label="条形码：")
        barcode_input = wx.SearchCtrl(dlg, style=wx.TE_PROCESS_ENTER)
        input_sizer = wx.BoxSizer(wx.HORIZONTAL)
        input_sizer.Add(barcode_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        input_sizer.Add(barcode_input, 1, wx.ALL | wx.EXPAND, 5)
        sizer.Add(input_sizer, 0, wx.ALL | wx.EXPAND, 5)

        # 在创建按钮部分添加确定按钮
        query_button = wx.Button(dlg, label="查询")
        confirm_button = wx.Button(dlg, label="确定执行出库")  # 新增确定按钮

        # 调整布局，将查询和确定按钮放在同一行
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(query_button, 0, wx.ALL, 5)
        button_sizer.Add(confirm_button, 0, wx.ALL, 5)
        sizer.Add(button_sizer, 0, wx.ALL | wx.ALIGN_CENTER, 5)  # 替换原单独添加的query_button

        # 信息列表
        list_ctrl = wx.ListCtrl(dlg, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_NONE | wx.LC_HRULES | wx.LC_VRULES)
        list_ctrl.InsertColumn(0, "物品名称")
        list_ctrl.InsertColumn(1, "条形码")
        list_ctrl.InsertColumn(2, "当前库存")
        list_ctrl.InsertColumn(3, "减少库存")
        list_ctrl.SetColumnWidth(0, 150)
        list_ctrl.SetColumnWidth(1, 150)
        list_ctrl.SetColumnWidth(2, 100)
        list_ctrl.SetColumnWidth(3, 100)
        sizer.Add(list_ctrl, 1, wx.ALL | wx.EXPAND, 5)

        def on_query(evt):
            barcode = barcode_input.GetValue().strip()
            if not barcode:
                wx.MessageBox('请输入条形码!', '温馨提示', wx.YES_DEFAULT | wx.ICON_EXCLAMATION)
                return

            try:
                goods_num = Fraction(1)  # 每次减少库存默认为1
            except:
                dial = wx.MessageDialog(dlg, '输入的商品数量有误，应为整数(1)或小数(1.2)或分数(1/12)', '温馨提示', wx.OK)
                dial.ShowModal()
                dial.Destroy()
                return

            # 根据条形码查询物品信息
            goods_info_list = goodsservice.get_goods_by_barcode_exact(barcode)
            if not goods_info_list:
                winsound.Beep(2000, 800)
                wx.MessageBox('未找到该条形码对应的物品信息!', '温馨提示', wx.YES_DEFAULT | wx.ICON_EXCLAMATION)
                return

            goods_info = goods_info_list[0]  # 假设条形码唯一，取第一条记录
            goods_name = goods_info['GOODS_NAME']
            goods_id = goods_info['ID']
            current_stock = goodsservice.get_goods_stock(goods_id)


            if current_stock < goods_num:
                dial = wx.MessageDialog(dlg, '库存不足,当前库存为{}'.format(current_stock), '温馨提示', wx.OK)
                dial.ShowModal()
                dial.Destroy()
                return

            if barcode in self.out_stock_items:
                index, _, _, reduce_stock = self.out_stock_items[barcode]
                new_reduce_stock = reduce_stock + goods_num
                list_ctrl.SetItem(index, 3, str(new_reduce_stock))
                self.out_stock_items[barcode] = (index, goods_name, current_stock, new_reduce_stock)
            else:
                index = list_ctrl.InsertItem(list_ctrl.GetItemCount(), goods_name)
                list_ctrl.SetItem(index, 1, barcode)
                list_ctrl.SetItem(index, 2, str(current_stock))
                list_ctrl.SetItem(index, 3, str(goods_num))
                self.out_stock_items[barcode] = (index, goods_name, current_stock, goods_num)

            #扫码成功提示音
            winsound.MessageBeep(winsound.MB_OK)

            barcode_input.SetValue("")  # 清空输入框

        query_button.Bind(wx.EVT_BUTTON, on_query)
        barcode_input.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, on_query)  # 绑定搜索按钮事件
        barcode_input.Bind(wx.EVT_TEXT_ENTER, on_query)  # 绑定回车键事件

        confirm_button.Bind(wx.EVT_BUTTON, self.OnConfirmOutStock)  # 绑定事件

        dlg.SetSizer(sizer)
        dlg.CenterOnParent()
        dlg.ShowModal()
        dlg.Destroy()
    def SaveStock(self, stock_type):
        if self.goodsId is None:
            wx.MessageBox('请在左侧选择要登记的物品!', '温馨提示', wx.YES_DEFAULT | wx.ICON_EXCLAMATION)
            return

        # 输入值校验
        try:
            goodnum = Fraction(self.tc_goodsNum.GetValue())
        except:
            dial = wx.MessageDialog(self, '输入的商品数量有误，应为整数(1)或小数(1.2)或分数(1/12)'.format(self.currentinventory), '温馨提示', wx.OK)
            dial.ShowModal()
            dial.Destroy()
            return ''
        if goodnum is None :
            wx.MessageBox('请输入物品数量!', '温馨提示', wx.YES_DEFAULT | wx.ICON_EXCLAMATION)
            self.tc_goodsNum.SetBackgroundColour("pink")
            self.tc_goodsNum.SetFocus()
            self.tc_goodsNum.Refresh()
            return
        # elif goodnum < '1':
        #     wx.MessageBox('物品数量至少为1', '温馨提示', wx.YES_DEFAULT | wx.ICON_EXCLAMATION)
        #     self.tc_goodsNum.SetBackgroundColour("pink")
        #     self.tc_goodsNum.SetFocus()
        #     self.tc_goodsNum.Refresh()
        #     return
        else:
            self.tc_goodsNum.SetBackgroundColour(
                wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
            self.tc_goodsNum.Refresh()
            
        goodunit = self.tc_goodsunit.GetValue().strip()
        if goodunit is None or goodunit  == '':
            wx.MessageBox('请输入物品规格!', '温馨提示', wx.YES_DEFAULT | wx.ICON_EXCLAMATION)
            self.tc_goodsunit.SetBackgroundColour("pink")
            self.tc_goodsunit.SetFocus()
            self.tc_goodsunit.Refresh()
            return
        else:
            self.tc_goodsunit.SetBackgroundColour(
                wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
            self.tc_goodsunit.Refresh()

        stock_date = self.op_date.GetValue().Format('%Y-%m-%d')
        goods_id = self.goodsId
        goodunit = self.tc_goodsunit.GetValue().strip()
        goodprice = self.tc_goodsprice.GetValue().strip()
        if goodprice !='':
            pattern= re.compile('^[0-9]*\.?[0-9]{,2}$')
            if re.match(pattern,goodprice ) is None:
                wx.MessageBox('单价不符合要求的格式', '温馨提示', wx.YES_DEFAULT | wx.ICON_EXCLAMATION)
                return

        goods_num = self.tc_goodsNum.GetValue()

        op_person = self.tc_op.GetValue().strip()
        op_area = self.tc_address.GetValue().strip()
        
        params = {
            'STOCK_TYPE': stock_type,
            'STOCK_DATE': stock_date,
            'GOODS_ID': goods_id,
            'GOODS_NUM': goods_num,
            'GOODS_UNIT': goodunit,
            'GOODS_PRICE': goodprice,
            'OP_PERSON': op_person, 
            'OP_AREA': op_area
            }
        
        stockservice.add_stock(params)
        wx.MessageBox('物品登记成功!', '温馨提示', wx.OK|wx.ICON_INFORMATION)
        self.queryStocksByDate()

    def OnDelete(self, event):
        count = self.list.SelectedItemCount
        if count < 1:
            dial = wx.MessageDialog(self, '请选择要删除的记录!', '温馨提示', wx.OK)
            dial.ShowModal()
            dial.Destroy()
        else:
            dlg = wx.MessageDialog(None, u"确定要删除该条记录吗？删除将不可恢复", u"温馨提示", wx.YES_NO | wx.ICON_QUESTION)
            if dlg.ShowModal() == wx.ID_YES:
                index = self.list.GetFirstSelected()
                item = self.list.GetItem(index)
                stockId = item.GetData()

                result = stockservice.delete_stock(stockId)
                if result > 0:
                    self.list.DeleteItem(index)
                    dial = wx.MessageDialog(self, '记录已经成功删除!', '温馨提示', wx.OK)
                    dial.ShowModal()
                    dial.Destroy()
            dlg.Destroy()


    def setData(self, data):
        self.list.DeleteAllItems()
        self.list.data = data
        for idx , row in enumerate(data):
            index = self.list.InsertItem(self.list.GetItemCount(), str(idx+1))
            for col, text in enumerate(row[1:]):
                if not text:
                    text = ''
                if col == 0:
                    text = '入库' if text == 1 else '出库'
                self.list.SetItem(index, col+1, str(text))
            self.list.SetItemData(index, row[0]) 

        self.list.SetColumnWidth(2, wx.LIST_AUTOSIZE)

    def OnFloatChar(self, evt):
        key = evt.GetKeyCode()
        if key < wx.WXK_SPACE or key == wx.WXK_DELETE or key > 255 or key==46:
            evt.Skip()
            return
        if chr(key).isdigit():
            evt.Skip()
            return
        return
    
    def OnReset(self,evt):
        self.goodsId = None
        self.tc_goodsname.SetValue('')
        self.tc_goodsunit.SetValue('')
        self.tc_goodsprice.SetValue('')
        self.tc_goodcatagory.SetValue('')
        self.tc_goodsNum.SetValue(None)
        self.tc_op.SetValue('')
        self.tc_address.SetValue('')
        self.op_date.SetValue(wx.DateTime.Today())
        
    def OnCalculate(self,evt):
        if self.tc_goodsNum.GetValue() != None and self.tc_goodsprice.GetValue() != None:
            totalamount = Fraction(self.tc_goodsNum.GetValue()) * float(self.tc_goodsprice.GetValue())
            self.tc_totalamount.SetValue(str(round(totalamount,2)))
class StockReportPanel(wx.Panel):
    def __init__(self, parent):
        super(StockReportPanel, self).__init__(parent, wx.ID_ANY, style=wx.CLIP_CHILDREN)
        
        self.InitUI()
        
    def InitUI(self):
        
        
        labelfont = wx.Font(wx.NORMAL_FONT.GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title_label = wx.StaticText(self, wx.ID_ANY, '查询条件')
        title_label.SetFont(labelfont)
        
        line1 = wx.StaticLine(self, wx.ID_ANY,size=(20,-1),style=wx.LI_HORIZONTAL)
        
        self.inStock_cb = wx.CheckBox(self, wx.ID_ANY, "入库", style=wx.ALIGN_RIGHT)
        self.outStock_cb = wx.CheckBox(self, wx.ID_ANY, "出库",style=wx.ALIGN_RIGHT)
        self.inStock_cb.SetValue(True)
        self.outStock_cb.SetValue(True)
        
        goodsname_label = wx.StaticText(self, wx.ID_ANY, '物品名称：')
        date_label = wx.StaticText(self, wx.ID_ANY, '起止日期：')
        concat_label = wx.StaticText(self, wx.ID_ANY, '至')
         
        self.goodsname_tc = wx.TextCtrl(self, wx.ID_ANY, size=(120,-1))
        self.goodsname_tc.SetMaxLength(16)
         
        self.startdate = wx.adv.DatePickerCtrl(self, size=(120,-1), style=wx.adv.DP_DROPDOWN| wx.adv.DP_SHOWCENTURY)
        self.startdate.SetRange(wx.DateTime.Today().Subtract(wx.DateSpan(months=6)), wx.DateTime.Today())
        self.startdate.SetValue(wx.DateTime.Today().Subtract(wx.DateSpan(days=6)))
                                
        self.endate = wx.adv.DatePickerCtrl(self, size=(120,-1),style=wx.adv.DP_DROPDOWN| wx.adv.DP_SHOWCENTURY)
        self.endate.SetRange(wx.DateTime.Today().Subtract(wx.DateSpan(months=6)), wx.DateTime.Today())
         
        gbSizer = wx.GridBagSizer(5, 5)
        gbSizer.Add(self.inStock_cb, (0,0), (1,1), wx.ALL, 5)
        gbSizer.Add(self.outStock_cb, (0,1), (1,1),wx.ALL, 5)
        gbSizer.Add(goodsname_label, (1,0), (1,1),wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
        gbSizer.Add(self.goodsname_tc, (1,1), (1,1),wx.ALL, 5)
        gbSizer.Add(date_label, (2,0), (1,1),wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
        gbSizer.Add(self.startdate, (2,1), (1,1),wx.ALL, 5)
        gbSizer.Add(concat_label, (2,2), (1,1),wx.ALL|wx.ALIGN_CENTER, 5)
        gbSizer.Add(self.endate, (2,3), (1,1),wx.ALL, 5)
        
        hBox_btn = wx.BoxSizer(wx.HORIZONTAL)
        hBox_btn.AddStretchSpacer()
        b = buttons.GenButton(self, -1, "查询")
        hBox_btn.Add(b, 0, wx.ALL, 5)
        self.Bind(wx.EVT_BUTTON, self.OnSearch, b)
        b = buttons.GenButton(self, -1, "导出EXCEL")
        self.Bind(wx.EVT_BUTTON, self.OnDownload, b)
        hBox_btn.Add(b, 0, wx.ALL, 5)
        hBox_btn.AddStretchSpacer()
        
        #grid
        self.grid = gridlib.Grid(self)
        table = StockDataTable([])
        self.grid.SetTable(table, True)
        self.grid.SetMargins(0,0)
        self.grid.AutoSizeColumns(True)
        
        vBox = wx.BoxSizer(wx.VERTICAL)
        vBox.Add(title_label, 0, wx.ALL, 5 )
        vBox.Add(line1, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL |
                  wx.RIGHT | wx.TOP, 0)
        vBox.Add(gbSizer, 0, wx.ALL, 5 )
        vBox.Add(hBox_btn, 0, wx.ALL|wx.EXPAND, 5 )
        vBox.Add(self.grid, 1, wx.GROW|wx.ALL, 5)
        
        self.SetSizer(vBox)
        
    def OnSearch(self, evt):
        goodsname = self.goodsname_tc.GetValue().strip()
        startdate = self.startdate.GetValue().Format('%Y-%m-%d')
        enddate = self.endate.GetValue().Format('%Y-%m-%d')

        params = {
                'goods_name':  '%' +goodsname+'%',
                'startdate': startdate,
                'enddate': enddate,
                'instock': self.inStock_cb.IsChecked(),
                'outstock': self.outStock_cb.IsChecked()
            }
        stocks = stockservice.get_stocks(params)
        
        table = StockDataTable(stocks)
        self.grid.SetTable(table, True)

        self.grid.SetMargins(0,0)
        self.grid.AutoSizeColumns(True)
        self.grid.Refresh()
        
    def OnDownload(self, evt):
        goodsname = self.goodsname_tc.GetValue().strip()
        startdate = self.startdate.GetValue().Format('%Y%m%d')
        enddate = self.endate.GetValue().Format('%Y%m%d')
        
        params = {
            'goods_name':  '%' +goodsname+'%',
            'startdate': self.startdate.GetValue().Format('%Y-%m-%d') ,
            'enddate': self.endate.GetValue().Format('%Y-%m-%d'),
            'instock': self.inStock_cb.IsChecked(),
            'outstock': self.outStock_cb.IsChecked()
        }
        data = stockservice.get_stocks_dict(params)
        if not data:
            wx.MessageBox("未查询到满足条件的结果，无法下载","温馨提示",wx.OK_DEFAULT|wx.ICON_WARNING)
            return 
        
        if self.inStock_cb.IsChecked() and not self.outStock_cb.IsChecked():
            filename_prefix = startdate + '至' + enddate + '入库明细表'
        elif not self.outStock_cb.IsChecked() and self.outStock_cb.IsChecked():
            filename_prefix = startdate + '至' + enddate + '出库明细表'
        else:
            filename_prefix = startdate + '至' + enddate + '出入库明细表'
            
        defaultFilename = filename_prefix + '.xlsx'
        wildcard = "Excel工作簿 (*.xlsx)|*.xlsx|All files (*.*)|*.*"
        dlg = wx.FileDialog(
                    self, message="保存为 ...", defaultDir=os.getcwd(),
                    defaultFile=defaultFilename, wildcard=wildcard, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
                    )
        dlg.SetFilterIndex(0)

        if dlg.ShowModal() == wx.ID_OK:
            try:
                self.Freeze()
                wx.BeginBusyCursor()
                path = dlg.GetPath()
        
                
                if self.inStock_cb.IsChecked() and not self.outStock_cb.IsChecked():
                    title = startdate + '至' + enddate + '入库明细表'
                    downloadservice.downloadInStockDetail(path, title, data)
                elif not self.outStock_cb.IsChecked() and self.outStock_cb.IsChecked():
                    title = startdate + '至' + enddate + '出库明细表'
                    downloadservice.downloadOutStockDetail(path, title, data)
                else:
                    title = startdate + '至' + enddate + '出入库明细表'
                    downloadservice.downloadAllStockDetail(path, title, data)
                    
            finally:
                self.Thaw()
                wx.EndBusyCursor()
        
class StockDataTable(gridlib.GridTableBase):
    
    def __init__(self, stockdata):
        super(StockDataTable, self).__init__()
        
        self.fieldDict = {
                '1' : '入库',
                '0': '出库'
            }
        
        self.colLabels = ['出库/入库', '物品类别', '物品名称', '登记日期',
                          '数量', '规格', '价格', '经办人','科室/地点']
        
        self.default_number_rows = 0
        self.default_number_cols = len(self.colLabels)
        self.data = stockdata
        
        self.odd=gridlib.GridCellAttr()
        self.odd.SetBackgroundColour("light blue")
        #self.odd.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.even=gridlib.GridCellAttr()
        self.even.SetBackgroundColour('Seashell')
        #self.even.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))

    def GetAttr(self, row, col, kind):
        attr = [self.even, self.odd][row % 2]
        attr.IncRef()
        return attr
    
    def GetColLabelValue(self, col):
        return self.colLabels[col]
    
    def GetNumberRows(self):
        
        if self.data :
            return len(self.data) + 1
        else:
            return self.default_number_rows

    def GetNumberCols(self):
        if self.data :
            return len(self.data[0])-1
        else:
            return self.default_number_cols

    def IsEmptyCell(self, row, col):
        try:
            return not self.data[row][col+1]
        except IndexError:
            return True
        
    def GetValue(self, row, col):
        try:
            if col==0:
                return self.fieldDict[str(self.data[row][col+1])]
            return self.data[row][col+1]
        except IndexError:
            return ''
        
    def SetValue(self, row, col, value):
        pass


class SockListCtrl(wx.ListCtrl,
                   listmix.ListCtrlAutoWidthMixin,
                   listmix.TextEditMixin):

    def __init__(self, parent, ID, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        super(SockListCtrl, self).__init__( parent, ID, pos, size, style)


        self.columns_labels = ['序号','类型', '物品类别','物品名称','登记日期','数量','规格','价格','经办人','经办地点']
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        self.Populate()
        listmix.TextEditMixin.__init__(self)

        self.data = None
        self.oldvalue = None

    def Populate(self):
        
        for col, text in enumerate(self.columns_labels ):
            self.InsertColumn(col, text)

        
    def OpenEditor(self, col, row):
        if col in [5,8,9]:
            
            listmix.TextEditMixin.OpenEditor(self, col, row)
            item = self.GetItem(self.curRow,self.curCol)
            self.oldvalue = item.GetText()
        else:
            pass

    def CloseEditor(self, evt=None):
        listmix.TextEditMixin.CloseEditor(self, evt)
        item = self.GetItem(self.curRow,self.curCol)
        newValue = item.GetText()
        oldValue = self.oldvalue
        if self.curCol == 5 :
            try:
                newValue = int(newValue)
            except ValueError:
                dial = wx.MessageDialog(self, '填写的必须是数字!', '温馨提示', wx.OK)
                dial.ShowModal()
                dial.Destroy()
                item.SetText(str(oldValue))
                self.SetItem(item)
                self.RefreshItem(self.curRow)
                return
        if str(newValue).strip() != str(oldValue).strip() :
            # 修改成功
            msg = '您将' + self.columns_labels[self.curCol] + '由[' + str(oldValue) + ']修改为[' + str(newValue) +']，确定要修改吗？'
            dlg = wx.MessageDialog(self, msg, u"温馨提示", wx.YES_NO | wx.ICON_QUESTION)
            if dlg.ShowModal() == wx.ID_YES:
                stockId = item.GetData()
                if self.curCol == 5:
                    sql = 'update stock set goods_num = ? where id = ? '
                elif self.curCol == 8:
                    sql = 'update stock set op_person = ? where id = ? '
                elif self.curCol == 9:
                    sql = 'update stock set op_area = ? where id = ? '
                params = ( newValue, stockId)
                db.update(sql, params)
            else:  
                item.SetText(str(oldValue))
                self.SetItem(item)
                self.RefreshItem(self.curRow)
            dlg.Destroy()
