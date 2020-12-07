# 간단한 서버 구축

#flask import
from flask import Flask

# Flask 인스턴스 생성
app=Flask(__name__)

@app.route('/')
def home():
    return 'aws 홈페이지'

# 서버로 가면 실제로는 작동 안함
# 외부에서 import로 사용하면 __name__이 '__main__'이 아니므로
# wsgi에서 import하게 되면 엔트리는 wsgi.py
# 이제는 패브릭을 설정한 룰에 의해 서버가 작동하게 됨
if __name__=='__main__':
    app.run(debug=True)