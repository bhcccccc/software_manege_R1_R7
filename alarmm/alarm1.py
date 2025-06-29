from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import pymysql
import time
from threading import Lock,Thread
from flask_cors import CORS
check_lock = Lock()
app = Flask(__name__, template_folder='../templates', static_folder='../static')
CORS(app)


socketio = SocketIO(app, cors_allowed_origins="*")
# MySQL connection configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'database': 'ocean',
}
# 初始为空规则，等待前端设置
alarm_rules = []

last_processed_id = None
check_in_progress = False  # 是否已经开始检查
threshold_received = False  # 是否已接收阈值

@app.route('/')
def index():
    return render_template('alarm.html')

@app.route('/login')
def tomain():
   return render_template('main.html')
@socketio.on('connect')
def handle_connect():
    print('Client connected')


@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')


@socketio.on('set_alarm_thresholds')
def handle_set_thresholds(data):
    global alarm_rules, threshold_received

    alarm_rules = [
        {'parameter': 'water_temperature',   'threshold': float(data.get('water_temperature', 0)),   'type': '>', 'message': '水温过高！'},
        {'parameter': 'pH',                    'threshold': 0,   'type': 'out_of_range', 'min': 6.5, 'max': 8.5, 'message': 'pH值超出正常范围！'},
        {'parameter': 'dissolved_oxygen',      'threshold': float(data.get('dissolved_oxygen', 0)),     'type': '<', 'message': '溶解氧过低！'},
        {'parameter': 'conductivity',          'threshold': float(data.get('conductivity', 0)),         'type': '>', 'message': '电导率过高！'},
        {'parameter': 'turbidity',             'threshold': float(data.get('turbidity', 0)),            'type': '>', 'message': '浊度过高！'},
        {'parameter': 'permanganate_index',    'threshold': float(data.get('permanganate_index', 0)),   'type': '>', 'message': '高锰酸盐指数过高！'},
        {'parameter': 'ammonia_nitrogen',      'threshold': float(data.get('ammonia_nitrogen', 0)),     'type': '>', 'message': '氨氮含量过高！'},
        {'parameter': 'total_phosphorus',      'threshold': float(data.get('total_phosphorus', 0)),     'type': '>', 'message': '总磷含量过高！'},
        {'parameter': 'total_nitrogen',        'threshold': float(data.get('total_nitrogen', 0)),       'type': '>', 'message': '总氮含量过高！'}
    ]

    threshold_received = True
    print("阈值已接收并更新规则。")
    emit('threshold_set_confirmation', {'status': 'success'})

def save_alarm_record(date, location, parameter, message):
    try:
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()
        
        query = "INSERT INTO alarms (alarm_date, location, parameter, message) VALUES (%s, %s, %s, %s)"
        values = (date, location, parameter, message)
        
        cursor.execute(query, values)
        conn.commit()
        print('Alarm record saved successfully.')
    except Exception as e:
        print(f"Error saving alarm record: {e}")
    finally:
        if conn.open:
            cursor.close()
            conn.close()
def check_water_data():
    global last_processed_id
    try:
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        if last_processed_id is not None:
            query = "SELECT * FROM water WHERE id > %s ORDER BY id ASC LIMIT 1"
            cursor.execute(query, (last_processed_id,))
        else:
            query = "SELECT * FROM water ORDER BY id ASC LIMIT 1"
            cursor.execute(query)

        latest_data = cursor.fetchone()

        if not latest_data:
            print("No more data to process.")
            return

        current_id = latest_data['id']
        location = latest_data['location']  # 获取 location
        print(f"Processing ID: {current_id}")

        for rule in alarm_rules:
            value = latest_data.get(rule['parameter'])

            if value is None:
                print(f"Warning: missing parameter '{rule['parameter']}' in record ID {current_id}")
                continue

            condition_met = False
            try:
                if rule['type'] == '>':
                    condition_met = value > rule['threshold']
                elif rule['type'] == '<':
                    condition_met = value < rule['threshold']
                elif rule['type'] == 'out_of_range':
                    condition_met = value < rule['min'] or value > rule['max']

            except TypeError as te:
                print(f"Error comparing {value} with threshold {rule['threshold']}: {te}")
                continue

            if condition_met:
                param_name_map = {
                    'water_temperature': '水温',
                    'pH': 'pH值',
                    'dissolved_oxygen': '溶解氧',
                    'conductivity': '电导率',
                    'turbidity': '浊度',
                    'permanganate_index': '高锰酸盐指数',
                    'ammonia_nitrogen': '氨氮',
                    'total_phosphorus': '总磷',
                    'total_nitrogen': '总氮'
                }

                operator_map = {
                    '>': '超过阈值',
                    '<': '低于阈值',
                    'out_of_range': '超出正常范围'
                }

                param_name = param_name_map.get(rule['parameter'], rule['parameter'])
                operator = operator_map.get(rule['type'], '异常')
                if rule['type'] == 'out_of_range':
                    alarm_message = f"[{location}] {param_name} 异常：{value}，不在正常范围 ({rule['min']}~{rule['max']})"
                else:
                    alarm_message = f"[{location}] {param_name} {operator}，当前值：{value}"

                print(f"[ALARM] {alarm_message}")
                
                socketio.emit('new_alarm', {'message': alarm_message})
                
                save_alarm_record(latest_data['date'], location, rule['parameter'], alarm_message)
        last_processed_id = current_id

    except Exception as e:
        print(f"Error checking water data: {e}")
    finally:
        if conn.open:
            cursor.close()
            conn.close()

def run_periodic_check():
    global threshold_received, check_in_progress
    check_in_progress = True

    while True:
        if threshold_received:
            check_water_data()
        socketio.sleep(1)  # 使用 socketio.sleep 支持异步环境


def start_background_task():
    monitor_thread = Thread(target=run_periodic_check, daemon=True)
    monitor_thread.start()
def start_alarm_server():
    print("Starting water data monitoring system...")

    # 启动后台任务
    socketio.start_background_task(run_periodic_check)

    # 启动 Flask-SocketIO 服务器
    socketio.run(app, debug=False, port=3000)

if __name__ == '__main__':
    
    print("Starting water data monitoring system...")

    # 启动后台线程，但一开始不会真正检查数据，直到收到阈值
    socketio.start_background_task(run_periodic_check)
    # 运行 Flask 应用
    socketio.run(app, debug=False, port=3000)

# alarm.py 中新增如下函数




