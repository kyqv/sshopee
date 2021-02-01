#coding=utf-8  
import sqlite3, json, os, requests, time
import machine_gun
from shopee_api import mydb
from bs4 import BeautifulSoup

def file_process():
    root_path = r"C:\Users\guoliang\Downloads\shopee 11月 账单"
    file_names = os.listdir(root_path)
    for f in file_names:
        od = "\\".join([root_path, f])
        si = od[-6:-4] + "_"
        nd = "\\".join([root_path, si + f])
        print(od, nd)
        #os.rename(od, nd)

def logit(logfile='out.log'):
    def logging_decorator(func):
        @wraps(func)
        def wrapped_function(*args, **kwargs):
            log_string = func.__name__ + " was called"
            print(log_string)
            # 打开logfile，并写入内容
            with open(logfile, 'a') as opened_file:
                # 现在将日志打到指定的logfile
                opened_file.write(log_string + '\n')
            return func(*args, **kwargs)
        return wrapped_function
    return logging_decorator

def stock2csv():
    import pandas
    p = 'C:/Users/guoliang/Desktop/库存1-27 -.xlsx'
    print(time.ctime())
    df = pandas.read_excel(p, engine='openpyxl')
    print(time.ctime())
    df = df.query('备货仓库="本地中国仓库"')
    cols = ['自定义SKU', '可用库存数', '库存结余数', '本仓估算日销量']
    df = df.filter(items=cols)
    df.to_csv('C:/Users/guoliang/Desktop/put.csv', index=False,)
    print(time.ctime())

def erp2stock():
    con = mydb("select sku from stock where ado > 5 limit 5;")
    sku_list = [i[0] for i in con]
    sku_list = ",".join(sku_list)

    ev = '''<?xml version="1.0" encoding="utf-8"?>
    <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
    <GetProducts xmlns="http://tempuri.org/">
    <productRequest>
    <CustomerID>1551</CustomerID>
    <UserName>guoliang</UserName>
    <Password>gl23r42</Password>
    <ClientSKUs>{sku_list}</ClientSKUs>
    </productRequest>
    </GetProducts>
    </soap:Body>
    </soap:Envelope>'''.format(sku_list=sku_list)
    print(sku_list)
    headers = {"content-type" : "text/xml; charset=utf-8"}
    url = "http://runbu.irobotbox.com/Api/API_ProductInfoManage.asmx"
    res = requests.post(url, data=ev, headers=headers)
    sp = BeautifulSoup(res.text, 'xml')
    rs = sp("ApiProductInfo")
    for row in rs:
        ClientSKU = row.find("ClientSKU").getText()
        ProductNameCN = row.find("ProductNameCN").getText()
        WithBattery = row.find("WithBattery").getText()
        ProductState = row.find("ProductState").getText()
        LastBuyPrice = row.find("LastBuyPrice").getText()
        GrossWeight = row.find("GrossWeight").getText()
        GoodNum = row.find("GoodNum").getText()
        AvgDailySales = row.find("AvgDailySales").getText()
        print(ClientSKU, ProductNameCN, WithBattery, ProductState, LastBuyPrice,
        GrossWeight,GoodNum,AvgDailySales)



def xlsx2stock(account):
    site = account[-2:]
    host = 'https://seller.{}.shopee.cn'.format(site)
    con = mydb('select cookies from cookies where account = ?', (account,))
    cookies = json.loads(con[0][0])
    file_name = '2restock_{}.xlsx'.format(account)
    file_path = 'D:/Downloads/{}'.format(file_name)
    url = host + '/api/tool/mass_product/upload_edit_template/?SPC_CDS_VER=2'
    files = {'file': (file_name, open(file_path, 'rb'),'application/vnd.ms-excel')}
    res = requests.post(url, files=files, cookies=cookies)
    print(res.json())
    url = host + '/api/tool/mass_product/get_mass_record_list/?SPC_CDS_VER=2&page_number=1&page_size=10&operation_type=4'
    res = requests.get(url, cookies=cookies)
    msg = res.json()['data']['list'][0]
    print(msg)



account, item_id, model_id, stock = "machinehome.sg", 5409941832, 41914362299, 80
con = mydb('select cookies from cookies where account = ?', (account,))
cookies = json.loads(con[0][0])
site = account[-2:]
host = "https://seller.{}.shopee.cn".format(site)
url = host + "/api/v3/product/get_product_detail"
params = "/?SPC_CDS_VER=2&product_id=" + str(item_id)
res = requests.get(url + params, cookies=cookies)
data = res.json()['data']

mych = [{"size":0,"price":"5.00","cover_shipping_fee":False,"enabled":True,"item_flag":"0","channelid":28016,"sizeid":0}]
idch = [{"size":0,"price":"10000.00","cover_shipping_fee":False,"enabled":True,"item_flag":"0","channelid":88001,"sizeid":0}]
sgch = [{"size":0.02,"price":"0.00","cover_shipping_fee":False,"enabled":True,"item_flag":"0","channelid":18028,"sizeid":0},
{"size":0.02,"price":"1.00","cover_shipping_fee":False,"enabled":True,"item_flag":"0","channelid":18025,"sizeid":0}]
udata = {"unlisted":False, "ds_cat_rcmd_id":""}
udata["logistics_channels"] = mych
ks = ["id","name","brand","images","description","model_list","category_path","attribute_model",
      "category_recommend","stock","price","price_before_discount","parent_sku","wholesale_list",
      "installment_tenures","weight","dimension","pre_order","days_to_ship","condition","size_chart",
      "tier_variation","add_on_deal"]
for k in ks:
    udata[k] = data[k]

if len(data['model_list']) == 0:
    udata['stock'] = stock
else:
    nms = [];
    for  m in udata['model_list']:
        if m['id'] == model_id:
            udata['stock'] += stock - m['stock']
            m['stock'] = stock
        nm = {}
        mks = ["id", "name", "price", "sku", "stock", "tier_index"]
        for mk in mks:
            nm[mk] = m[mk]
        nms.append(nm)
    udata['model_list'] = nms

updata = [udata,];
uurl = host + "/api/v3/product/update_product/?version=3.1.0&&SPC_CDS_VER=2"
res = requests.post(uurl, json=updata, cookies=cookies)
print(uurl, updata)
print(res.json())
