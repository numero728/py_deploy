"""
이름은 자유롭게 구성이 가능
wsgi라는 의미는 특정 플랫폼이 웹서비스가 가능할 때 wsgi 모듈이 지원된다.
flask, django -> 단독으로 서비스하는 것보다, 아파치/nginx라는 웹서버와 연동하여 주로 서비스
아파치 서버가 바라보는 엔트리 포인트(시작되는 파이썬 파일)로 wsgi.py 지정
"""

import sys
import os

# 현재 경로
cur_dir=os.getcwd()
cur_dir

# 에러 출력을 표준출력으로 보낸다.
sys.stdout=sys.stderr

# 시스템이 이 파일을 이해할 수 있도록 시스템의 경로에 현 디렉토리의 경로를 삽입
sys.path.insert(0,cur_dir)

# 서버 가동을 위한 모듈 가져오기
from run import app



