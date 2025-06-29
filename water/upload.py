import pymysql
from water import water
from tqdm import trange

def update_water(waters,db_config):
    connection = pymysql.connect(**db_config)
    cursor = connection.cursor()
    table_name = 'water'
    sql = f"TRUNCATE TABLE {table_name}"
    cursor.execute(sql)
    connection.commit()
    print(f"表 {table_name} 已清空")
    cursor.close()
    connection.close()
    connection = pymysql.connect(**db_config)
    cursor = connection.cursor()
    for i in trange(len(waters)):
        water = waters[i]
        str1,str2=water.str()
        str = f"INSERT INTO water {str1} VALUES {str2}"
        try:
            cursor.execute(str)
            connection.commit()
        except Exception as e:
            print(f"An error occurred: {e}")
            connection.rollback()
            print(str)
    cursor.close()
    connection.close()

def upload_water(water,connection,cursor):
    str1, str2 = water.str()
    str = f"INSERT INTO water {str1} VALUES {str2}"
    try:
        cursor.execute(str)
        connection.commit()
    except Exception as e:
        print(f"An error occurred: {e}")
        connection.rollback()
        print(str)
        return
    #print(f"right upload!\n{str}\n")

if __name__=="__main__":
    db_config = {
        "host": "localhost",  # 数据库地址
        "port": 3306,  # 数据库端口，默认是3306
        "user": "root",  # 数据库用户名
        "password": "1231",  # 数据库密码
        "database": "ocean",  # 要连接的数据库名
        "charset": 'utf8mb3'  # 字符集，推荐使用utf8mb4以支持emoji等字符
    }