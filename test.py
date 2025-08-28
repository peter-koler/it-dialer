from flask import Flask, request, jsonify
import socket

app = Flask(__name__)

@app.route('/ip', methods=['GET'])
def get_ip():
    """
    返回本机的IP地址
    """
    try:
        # 获取本机主机名
        hostname = socket.gethostname()
        # 通过主机名获取IP地址
        ip_address = socket.gethostbyname(hostname)
        return jsonify({'ip': ip_address})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/name', methods=['GET'])
def get_hostname():
    """
    根据传入的IP地址获取主机名
    参数: ip - 要查询的IP地址
    """
    try:
        ip_address = request.args.get('ip')
        if not ip_address:
            return jsonify({'error': 'IP address parameter is required'}), 400
        
        # 通过IP地址获取主机名
        hostname = socket.gethostbyaddr(ip_address)[0]
        return jsonify({'hostname': hostname})
    except socket.herror as e:
        return jsonify({'error': 'Hostname not found for the given IP'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6000, debug=True)