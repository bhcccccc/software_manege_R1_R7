import csv
from water import water
import re
import glob
from datetime import datetime
from upload import update_water

def findFiles(path,recursive=False):
    return glob.glob(path,recursive=recursive)

def calc(str):
    if str=='--' or str=='*':
        return None
    else:
        return eval(str)

if __name__ == "__main__":
    data_paths=findFiles("**/*.csv",True)
    db_config = {
        "host": "localhost",  # 数据库地址
        "port": 3306,  # 数据库端口，默认是3306
        "user": "root",  # 数据库用户名
        "password": "123456",  # 数据库密码
        "database": "ocean",  # 要连接的数据库名
        "charset": 'utf8mb3'  # 字符集，推荐使用utf8mb4以支持emoji等字符
    }
    datas=[]
    for data_path in data_paths:
        match = re.search(r'(\d{4})-\d{2}', data_path)
        year=None
        if match:
            year = match.group(1)
        else:
            print("error in year")
            continue
        with open(data_path, 'r',encoding='utf-8') as file:
            reader=csv.reader(file)
            fir=0
            for row in reader:
                if fir==0:
                    fir=1
                    continue
                else:
                    if row[3]!='*' and row[3]!='--':
                        date_obj = datetime.strptime(f"{year}-{row[3]}", "%Y-%m-%d %H:%M")
                        a=water(row[0],row[2],date_obj)
                    else:
                        a = water(row[0], row[2])
                    a.water_temperature=calc(row[5])
                    a.pH = calc(row[6])
                    a.dissolved_oxygen = calc(row[7])
                    a.conductivity = calc(row[8])
                    a.turbidity = calc(row[9])
                    a.permanganate_index = calc(row[10])
                    a.ammonia_nitrogen = calc(row[11])
                    a.total_phosphorus = calc(row[12])
                    a.total_nitrogen = calc(row[13])
                    if row[-1]!='*' and row[-1]!='--':
                        a.site_condition=row[-1]
                    datas.append(a)
    update_water(datas,db_config)