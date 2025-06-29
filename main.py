from flask import Flask, request, send_from_directory, render_template,jsonify, redirect, url_for, flash,send_file, make_response, session
import io
import pymysql
from pymysql import Error
import multiprocessing
import subprocess
from water.water import water
from water.upload import upload_water
from io import StringIO
import csv
import os
import numpy as np
from werkzeug.utils import secure_filename
import tensorflow as tf
from tensorflow.keras.layers import Input, Conv2D, BatchNormalization, Activation, Add, AveragePooling2D, Flatten, Dense
from tensorflow.keras.models import Model
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
# 导入 alarm.py 中的函数
from alarmm.alarm1 import start_alarm_server
student_id="2213634"
student_id="2213634_2"
password='123456'

nowusername=''
nowrole=''

IMG_HEIGHT = 224
IMG_WIDTH = 224
class_names =  ['海鲈鱼', '红海鲷鱼', '红鲻鱼', '银鳍鲷', '马鲛鱼', '鳟鱼', '黑海鳀鱼']
best_model = tf.keras.models.load_model('../best_model.h5')
best_model1 = tf.keras.models.load_model('../best_model1.h5')


# 请确保您已将 API Key 存储在环境变量 ARK_API_KEY 中
# 初始化Ark客户端，从环境变量中读取您的API Key

# 定义一个函数来预测单张图像的体长
def predict_fish_length(image_path):
    img = tf.keras.utils.load_img(image_path, target_size=(IMG_HEIGHT, IMG_WIDTH))
    img_array = tf.keras.utils.img_to_array(img)
    img_array = tf.expand_dims(img_array, 0)  # 创建批次维度
    img_array = img_array / 255.0  # 归一化

    prediction = best_model1.predict(img_array)
    return prediction[0][0]  # 返回预测的体长
# 定义一个函数来预测单张图像
def predict_fish(image_path):
    img = tf.keras.utils.load_img(image_path, target_size=(IMG_HEIGHT, IMG_WIDTH))
    img_array = tf.keras.utils.img_to_array(img)
    img_array = tf.expand_dims(img_array, 0)  # 创建批次维度
    img_array = img_array / 255.0  # 归一化

    predictions = best_model.predict(img_array)
    predicted_class = np.argmax(predictions[0])
    confidence = np.max(predictions[0])

    return class_names[predicted_class], confidence

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/')
def start():
    return render_template('login.html')
@app.route('/a')
def alarm():
    return render_template('alarm.html')
@app.route('/exit')
def exit():
    return render_template('login.html')
@app.route('/turn_to_register',methods=['POST','GET'])
def turn_to_register():
   return render_template('register.html')

@app.route('/location')
def location():
    province = request.args.get('province')
    str=f"SELECT province, location FROM water WHERE province = \"{province}\" GROUP BY province, location"
    cursor.execute(str)
    locations = [(row['location']) for row in cursor]
    return render_template('location.html', username=nowusername,locations=locations,province=province,userrole=nowrole)
@app.route('/juti')
def juti():
    province = request.args.get('province')
    location = request.args.get('location')
    str=f"SELECT * FROM water WHERE location = \"{location}\" AND province = \"{province}\" GROUP BY id ORDER BY id"
    cursor.execute(str)
    datas=[]
    for row in cursor:
        row_list = [val if val else "-" for val in row.values()]
        datas.append(row_list)
    return render_template('juti.html', username=nowusername,datas=datas,userrole=nowrole)

@app.route('/toadadmin')
def toadadmin():
   cursor.execute("SELECT * FROM user")
   users = cursor.fetchall()
   return render_template('ad_admin.html',username=nowusername,users=users,userrole=nowrole)
@app.route('/add_user',methods=['POST'])
def add_user():
    username = request.form['username']
    password = request.form['password']
    role = request.form['role']
    
    cursor.execute("INSERT INTO user (username, password, role) VALUES (%s, %s, %s)", (username, password, role))
    connection.commit()
    flash('用户添加成功')
    return redirect(url_for('toadadmin'))
@app.route('/toadduser')
def toadduser():
      
        return render_template('editor.html')
@app.route('/edit_user/<int:id>',methods=['POST'])
def edit_user(id):
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        cursor.execute("UPDATE user SET username = %s, password = %s, role = %s WHERE userid = %s", (username, password, role, id))
        connection.commit()
        flash('用户更新成功')
        return redirect(url_for('toadadmin'))


@app.route('/toaddwater')
def toaddwater():
    return render_template('upload_water.html')


@app.route('/delete_water_data', methods=['POST'])
def delete_water_data():
    data_id = request.form.get('data_id')
    try:
        cursor.execute("DELETE FROM water WHERE id = %s", (data_id,))
        connection.commit()

        # 检查是否成功删除
        if cursor.rowcount > 0:
            return jsonify({'status': 'success', 'message': '数据删除成功！'})
        else:
            return jsonify({'status': 'error', 'message': '未找到对应的数据ID！'})
    except Exception as e:
        connection.rollback()
        print(1)
        return jsonify({'status': 'error', 'message': f'删除失败: {str(e)}'})

@app.route('/upload_water',methods=['POST'])
def upload_data():
    province = request.form.get('province', None)
    location = request.form.get('location', None)
    date = request.form.get('monitor_time', None)
    water_temperature = request.form.get('water_temp', None)
    pH = request.form.get('ph', None)
    dissolved_oxygen = request.form.get('dissolved_oxygen', None)
    conductivity = request.form.get('conductivity', None)
    turbidity = request.form.get('turbidity', None)
    permanganate_index = request.form.get('permanganate_index', None)
    ammonia_nitrogen = request.form.get('ammonia_nitrogen', None)
    total_phosphorus = request.form.get('total_phosphorus', None)
    total_nitrogen = request.form.get('total_nitrogen', None)
    site_condition = request.form.get('status', None)
    data=water(province,location,date,water_temperature,pH,dissolved_oxygen,conductivity,turbidity,permanganate_index,ammonia_nitrogen,total_phosphorus,total_nitrogen,site_condition)
    upload_water(data,connection,cursor)
    flash('水文数据添加成功')
    return redirect(url_for('toadadmin'))

@app.route('/download_water_data')
def download_water_data():
    try:
        # 查询 water 表的数据
        cursor.execute("SELECT * FROM water ORDER BY id")
        data = cursor.fetchall()

        columns = data[0].keys()

        # 创建内存中的 CSV 文件
        si = StringIO()
        writer = csv.DictWriter(si, fieldnames=columns)
        writer.writeheader()
        for row in data:
            writer.writerow(row)
        ansi_content = si.getvalue().encode('gbk', errors='ignore')
        # 创建响应对象
        output = make_response(ansi_content)
        output.headers["Content-Disposition"] = "attachment; filename=water_data.csv"
        output.headers["Content-type"] = "text/csv"

        return output

    except Exception as e:
        return f"下载失败: {str(e)}"

@app.route('/toedit/<int:id>')
def toedit(id):
        cursor.execute("SELECT * FROM user WHERE userid = %s", (id,))
        user = cursor.fetchone()
        return render_template('editor.html', user=user)

@app.route('/delete_user/<int:id>')
def delete_user(id):
    
    cursor.execute("DELETE FROM user WHERE userid = %s", (id,))
    connection.commit()

    flash('用户删除成功')
    return redirect(url_for('toadadmin'))
@app.route('/tomain')
def tomain():
   return render_template('main.html',username=nowusername,userrole=nowrole)
@app.route('/toai')
def toai():
   return render_template('ai.html',username=nowusername,userrole=nowrole)
@app.route('/todata')
def todata():
    cursor.execute("SELECT DISTINCT province FROM water")
    provinces = [row['province'] for row in cursor]
    return render_template('data.html', username=nowusername, provinces=provinces,userrole=nowrole)

@app.route('/towater')
def towater():
    fish_data = {}
    fish_types = []
    all_fish_records = []
    total_fish = 0
    try:
        cursor.execute("SELECT * FROM fish")
        records = cursor.fetchall()
        all_fish_records = records
        total_fish = len(records)  # 计算总鱼数
        for fish in records:
            ftype = fish['type']
            if ftype not in fish_data:
                fish_data[ftype] = []
                fish_types.append(ftype)
            avg_length = (fish['length1'] + fish['length2'] + fish['length3']) / 3
            fish_data[ftype].append({
                'length': avg_length,
                'height': fish['height']
            })
    except pymysql.MySQLError as e:
        print("数据库错误:", e)

    return render_template('water.html',
                        username=nowusername,
                           fish_data=fish_data,
                           fish_types=fish_types,
                           all_fish_records=all_fish_records,
                           total_fish=total_fish,       # 传总鱼数
                           env_score=70,
                           userrole=session.get('userrole'))

# 上传数据接口，只允许管理员
@app.route('/upload_fish_data', methods=['POST'])
def upload_fish_data():
    if session.get('userrole') != 'admin':
        flash('无权限上传数据')
        return redirect(url_for('towater'))

    if 'file' not in request.files:
        flash('未上传文件')
        return redirect(url_for('towater'))
    file = request.files['file']
    if file.filename == '':
        flash('未选择文件')
        return redirect(url_for('towater'))
    try:
        stream = io.StringIO(file.stream.read().decode("utf-8"))
        reader = csv.DictReader(stream)
        for row in reader:
            cursor.execute("""
                INSERT INTO fish (type, weight, length1, length2, length3, height, width) 
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE 
                    type=VALUES(type), weight=VALUES(weight), length1=VALUES(length1), 
                    length2=VALUES(length2), length3=VALUES(length3), height=VALUES(height), width=VALUES(width)
            """, (
                row['Species'], row['Weight(g)'], row['Length1(cm)'], row['Length2(cm)'], row['Length3(cm)'], row['Height(cm)'], row['Width(cm)']
            ))
        connection.commit()
        flash('数据上传成功')
    except pymysql.Error as e:
        connection.rollback()
        print(e)
        flash(f'上传失败: {e}')
    return redirect(url_for('towater'))

# 删除数据接口，只允许管理员
@app.route('/delete_fish_data', methods=['POST'])
def delete_fish_data():
    if session.get('userrole') != 'admin':
        flash('无权限删除数据')
        return redirect(url_for('towater'))

    fishid = request.form.get('fishid')
    if not fishid:
        flash('请填写要删除的fishid')
        return redirect(url_for('towater'))

    try:
        cursor.execute("DELETE FROM fish WHERE fishid = %s", (fishid,))
        connection.commit()
        flash(f'fishid={fishid} 删除成功')
    except Exception as e:
        connection.rollback()
        flash(f'删除失败: {e}')
    return redirect(url_for('towater'))

# 下载数据接口，所有用户可用
@app.route('/download_fish_data')
def download_fish_data():
    try:
        cursor.execute("SELECT fishid, type, weight, length1, length2, length3, height, width FROM fish")
        rows = cursor.fetchall()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['fishid', 'type', 'weight', 'length1', 'length2', 'length3', 'height', 'width'])
        for row in rows:
            writer.writerow([
                    row['fishid'], row['type'], row['weight'],
                    row['length1'], row['length2'], row['length3'],
                    row['height'], row['width']
                ])
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name='fish_data.csv'
        )
    except pymysql.Error as e:
        connection.rollback()
        print(e)
        flash(f'下载失败: {e}')
@app.route('/topersonal')
def topersonal():
   if 'nowusername' not in globals() or not nowusername:
        return render_template('login.html')
   return render_template('personal.html',username=nowusername, role=nowrole,userrole=nowrole)


#鱼类预测
@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        print(1)
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        print(2)
        return jsonify({'error': 'No selected file'}), 400
    
    if file :
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # 进行预测
        predicted_class, confidence = predict_fish(file_path)
        predicted_length = predict_fish_length(file_path)
        confidence=float(confidence)
        predicted_length=float(predicted_length)
        print(predicted_class)
        print(confidence)
        print(predicted_length)
        # 返回预测结果
        return jsonify({
            'fish_type': predicted_class,  # 示例：实际应用中可能需要从模型中获取
            'similarity': confidence,     # 示例：实际应用中可能需要从模型中获取
            'predicted_length': str(predicted_length) + ' cm'
        })
    print(1)
    return jsonify({'error': 'Invalid file format'}), 400
@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    question = data.get('question', '')
    print(question)
    response = fish_chat(question)
    
    print(response)
    return jsonify({"answer": response})


@app.route('/register',methods=['POST'])
def register():
    name = request.form['nm']
    password= request.form['pd']
    role=request.form['role']
    try:
        # 插入用户信息的 SQL 语句
        insert_query = "INSERT INTO user (username, password, role) VALUES (%s, %s, %s)"
        values = (name, password, role)

        # 执行 SQL 语句
        cursor.execute(insert_query, values)

        # 提交更改
        connection.commit()
        return render_template('login.html')
    except pymysql.Error as e:
        print(f"注册失败: {e}")
        return jsonify({"message": "用户名已存在"}), 409
    

@app.route('/login',methods=['POST'])
def login():
    global nowusername
    global nowrole
    name = request.form['nm']
    password= request.form['pd']
    cursor.execute("SELECT * FROM user WHERE username = %s AND password = %s", (name, password))
    user = cursor.fetchone()
    if user:
        nowusername=name
        nowrole=user['role']
        # 加入session
        session['userrole'] = user['role']
        session['username'] = name
        
       
        return render_template('main.html',username=nowusername,userrole=nowrole)
        
    else:
        return jsonify({"message": "用户名或密码错误"}), 401

@app.route('/change_name', methods=['POST'])
def change_name():
    global nowusername
    new_name = request.form['new_name'].strip()
    if not new_name:
        return jsonify({'message': '用户名不能为空'}), 400

    try:
        # 检查是否重名
        cursor.execute("SELECT userid FROM user WHERE username=%s", (new_name,))
        if cursor.fetchone():
            return jsonify({'message': '用户名已存在'}), 409

        # 更新数据库
        cursor.execute("UPDATE user SET username=%s WHERE username=%s",
                       (new_name, nowusername))
        connection.commit()

        # 更新当前会话中的用户名
        nowusername = new_name
        return jsonify({'message': '用户名修改成功'}), 200
    except pymysql.Error as e:
        print(f'修改用户名失败: {e}')
        return jsonify({'message': '服务器错误'}), 500
# 修改密码
@app.route('/change_pwd', methods=['POST'])
def change_pwd():
    old = request.form['old']
    new = request.form['new']
    confirm = request.form['confirm']

    if new != confirm:
        return jsonify({'message': '两次密码不一致'}), 400

    try:
        # 验证旧密码
        cursor.execute("SELECT password FROM user WHERE username=%s", (nowusername,))
        record = cursor.fetchone()
        if not record or record['password'] != old:
            return jsonify({'message': '旧密码错误'}), 403

        # 更新密码
        cursor.execute("UPDATE user SET password=%s WHERE username=%s",
                       (new, nowusername))
        connection.commit()
        return jsonify({'message': '密码修改成功'}), 200

    except pymysql.Error as e:
        print(f'修改密码失败: {e}')
        return jsonify({'message': '服务器错误'}), 500
if __name__ == '__main__':
    alarm_process = multiprocessing.Process(target=start_alarm_server)
    alarm_process.start()
    global connection
    global cursor
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password=password,
        database='ocean',
        cursorclass=pymysql.cursors.DictCursor
    )
    cursor = connection.cursor()
    app.run()
    
