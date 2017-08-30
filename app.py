import os
import tempfile
from pathlib import PurePath
import subprocess

from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://ddpguser:doordu.232!@#@10.0.0.70/doordu_manage'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
#app.config['SQLALCHEMY_ECHO'] = True
app.config['DEFAULT_SDK_APP_ID'] = '1400035141'             # 默认APPID
app.config['Your_SDK_APP_ID'] = 'dadd44f0426bb012'          # 权限密钥表
app.config['BINARY_PATH'] = os.path.join(os.path.dirname(__file__), 'bin')  # 执行文件目录
app.config['KEYS_PATH'] = os.path.join(os.path.dirname(__file__), 'keys') # keys目录

db = SQLAlchemy(app)


class UserModel(db.Model):
    __tablename__ = 'service_info'
    __table_args__ = {"schema":"service"}
    service_id = db.Column(db.Integer, primary_key=True)
    sip_no = db.Column(db.String(100))
    sip_pwd = db.Column(db.String(100))


@app.route('/login', methods=['POST'])
def login():
    request_params = request.get_json(force=True, silent=True)
    if request_params is None:
        abort(404)

    _id = request_params['id']
    pwd = request_params['pwd']
    appid = app.config.get('DEFAULT_SDK_APP_ID')

    user = UserModel.query.filter(UserModel.sip_no == _id).first()
    if user and user.sip_pwd == pwd:
        # 密码匹配, 进行签密
        """
        /data/website/SuiXinBoPHPServer/deps/bin/tls_licence_tools gen '/data/website/SuiXinBoPHPServer/deps/keys/1400035141/private_key' '/data/website/SuiXinBoPHPServer/deps/sig/sxb_sig.6bIVRYHc3e' '1400035141' '1001'
        """
        program_path = str(PurePath(app.config.get('BINARY_PATH'), 'tls_licence_tools'))
        private_key_path = str(PurePath(app.config.get('KEYS_PATH'), 'private_key'))
        file_description, tmpfile_path = tempfile.mkstemp(prefix='sxb_sig')
        os.close(file_description)
        ret = subprocess.check_call([program_path, 'gen', private_key_path, tmpfile_path, appid, _id])
        user_sig = open(tmpfile_path, 'r').read() # TODO: cache here
        os.unlink(tmpfile_path)
        return jsonify({'code': 0, 'data': {'userSig': user_sig}}), 200
    else:
        # 密码错误
        return jsonify({'code': -1, 'msg': '密码错误！'}), 404

    return jsonify({}), 200

if __name__ == "__main__":
    app.run(debug=True, use_reloader=True, host='0.0.0.0')
