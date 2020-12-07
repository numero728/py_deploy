#1. 모듈 가져오기
from fabric.contrib.files import append, exists, sed, put
from fabric.api import env, local, run, sudo
import os
import json

#2. 환경변수 관련 사항

# 현재 파일이 위치한 디렉토리 경로
# 리눅스: /home/ubuntu/deploy
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# 환경 변수 파일을 읽어서 로드하시오.
envs            = json.load(open(os.path.join(PROJECT_DIR, "deploy.json")))

# json 파일에 기록된 환경변수값들을 읽어서 변수에 담는다.
REPO_URL        = envs['REPO_URL']              # 저장소 위치
PROJECT_NAME    = envs['PROJECT_NAME']          # 프로젝트 이름
REMOTE_HOST     = envs['REMOTE_HOST']           # 원격 접속 주소
REMOTE_HOST_SSH = envs['REMOTE_HOST_SSH']       # 원격 접속 주소(SSH)
REMOTE_USER     = envs['REMOTE_USER']           # 원격 서버의 사용자명(ubuntu)

# envs는 딕셔너리, env.키=값 => env['키']=값 과 동일
env.user = REMOTE_USER
env.hosts = [
    REMOTE_HOST_SSH, # IP
]
env.use_ssh_config = True

# 서버에 접속하기 위해서 인증키를 위치시킨다.
env.key_filename = '../ai_flask.pem'

#/home/ubuntu/deploy
project_folder = '/home/{}/{}'.format(env.user, PROJECT_NAME)

# 리눅스를 새로 세팅하고 나서, 초기에 설치해야할 패키지들 목록
apt_requirements = [
    'curl',
    'git',
    'python3-dev',
    'python3-pip',
    'build-essential',
    'apache2',
    'libapache2-mod-wsgi-py3',
    'python3-setuptools',
    'libssl-dev',
    'libffi-dev',
]

#----------------------------------------------------------------(함수구간, 외부용 함수 = 패브릭 명령 수행 시 사용)------------------------------------------------------------------------




"""
최초 배포(최초 세팅 및 초기 배포 관련)


$ fab new_server

- 추후 업데이트(코드 수정작업 -> 배포)

$ fab deploy ; 초기 세팅이 없다.

"""




def new_server():
    setup()
    deploy()


def setup():
    # 운영체계상 os 업데이트에 관련된 사항 -> sudo apt-get update & upgrade 수행 위함
    _get_latest_apt()


    # os상에서 필요한 패키지 설치 -> for 문 이용하여 필요한 패키지들 모두 sudo apt-get으로 install 하는 명령어 수행
    _install_apt_requirements(apt_requirements)
    
    
    # flask 구동에 필요한 가상환경 구축
    _make_virtualenv()


def deploy():
    _get_latest_source()
    _put_envs()
    _update_virtualenv()
    _make_virtualhost()
    _grant_apache2()
    _restart_apache2()



#--------------------------------------------------------------------(_로 시작하는 함수 -> 내부에서만 사용 가능)
def _put_envs():
    pass  # activate for envs.json file
    # put('envs.json', '~/{}/envs.json'.format(PROJECT_NAME))

def _get_latest_apt():
    update_or_not = input('would you update?: [y/n]')
    if update_or_not == 'y':
        # 우분투 리눅스 명령
        # sudo 메서드를 통해 sudo 명령 사용가능
        # 패키지 관리자 업데이트, 업데이트된 내용 반영 -> 각종 패키지의 최신 저장소 갱신
        # 명령어 && 명령어
        # -y를 넣으면 무조건 동의한다는 의미(자동처리)
        sudo('apt-get update && apt-get -y upgrade')

def _install_apt_requirements(apt_requirements):
    reqs = ''
    # 설치할 패키지들을 한칸씩 띠어서 하나의 문자열로 만들고 있다.
    # 문자열을 포맷팅을 이용하여 하나의 sudo 명령문 생성
    # 우분투 리눅스에 구동 및 운영에 필요한 모든 패키지를 설치하는 명령
    for req in apt_requirements:
        reqs += (' ' + req)
    sudo('apt-get -y install {}'.format(reqs))

def _make_virtualenv():
    # 현재 디렉토리 상에서 ./virtualenvs 디렉토리가 존재하지 않으면
    if not exists('~/.virtualenvs'):
        # 리눅스상에서 환경 변수를 세팅 명령어(여러 줄, 문자열로 여러 줄 구성)
        script = '''"# python virtualenv settings
                    export WORKON_HOME=~/.virtualenvs
                    export VIRTUALENVWRAPPER_PYTHON="$(command \which python3)"  # location of python3
                    source /usr/local/bin/virtualenvwrapper.sh"'''
        
        # 디렉토리 생성: run() 운영체계에서 직접 수행
        run('mkdir ~/.virtualenvs')
        
        # sudo 메서드: 리눅스의 관리자 권한은 sudo
        # 즉, 관리자 권한으로 명령어 수행하라는 명령문
        # virtualenv => 기본적인 가상환경을 패키지, 아나콘다에 내장 
        sudo('pip3 install virtualenv virtualenvwrapper')

        # 위에서 작성한 스크립트(path)를 .bashrc라는 파일에 추가하시오.
        run('echo {} >> ~/.bashrc'.format(script))


# git를 통해서 배포하고자 하는 소스 코드 내려받는 파트
def _get_latest_source():
    # .git가 존재하면
    if exists(project_folder + '/.git'):

        # 프로젝트 폴더로 이동
        # git fetch를 통해서 최신 내용을 긁어온다.
        run('cd %s && git fetch' % (project_folder,))
    
    #.git가 없다면 -> 즉, 최초
    else:
        
        # 없으면 git clone 을 이용하여 소스를 카피해서 프로젝트 폴더에 둔다.
        run('git clone %s %s' % (REPO_URL, project_folder))

    # 최신 내용을 서버쪽에 저장
    current_commit = local("git log -n 1 --format=%H", capture=True)
    run('cd %s && git reset --hard %s' % (project_folder, current_commit))
    #run('cd %s && git reset --hard' % (project_folder, ))

def _update_virtualenv():
    # /home/ubuntu/
    # .git, .virtualenv, deploy, ..
    # virtualenv 디렉토리 안에(즉, 가상환경 안에) deploy 디렉토리 위치하고 이를 가상환경 폴더로 간주
    virtualenv_folder = project_folder + '/../.virtualenvs/{}'.format(PROJECT_NAME)
    if not exists(virtualenv_folder + '/bin/pip'):
        # 가상환경 폴더 안에 /bin/pip 존재하지 않으면
        # 가상환경을 만들어라
        # 아나콘다에서 새로 가상환경 세팅하는 것과 동일한 과정
        run('cd /home/%s/.virtualenvs && virtualenv %s' % (env.user, PROJECT_NAME))

    # 해당 가상환경에서 사용할 패키지를 설치하라.
    # pip install -r requirements.txt
    run('%s/bin/pip install -r %s/requirements.txt' % (
        virtualenv_folder, project_folder
    ))

def _ufw_allow():
    sudo("ufw allow 'Apache Full'")
    sudo("ufw reload")

# 아파치 서버 + flask 연동하여 서비스 운영
# 연동에 필요한 환경설정값
# wsgi.py가 엔트리포인트라는 부분, 포트가 80번(기본 http)
# 접속 로그, 에러 로그 위치 지정
# 하단의 구문들은 아파치 서버의 명령문이라 넘어가라
def _make_virtualhost():
    script = """'<VirtualHost *:80>
    ServerName {servername}
    <Directory /home/{username}/{project_name}>
        <Files wsgi.py>
            Require all granted
        </Files>
    </Directory>
    WSGIDaemonProcess {project_name} python-home=/home/{username}/.virtualenvs/{project_name} python-path=/home/{username}/{project_name}
    WSGIProcessGroup {project_name}
    WSGIScriptAlias / /home/{username}/{project_name}/wsgi.py
    
    ErrorLog ${{APACHE_LOG_DIR}}/error.log
    CustomLog ${{APACHE_LOG_DIR}}/access.log combined
    
    </VirtualHost>'""".format(
        username=REMOTE_USER,
        project_name=PROJECT_NAME,
        servername=REMOTE_HOST,
    )
    sudo('echo {} > /etc/apache2/sites-available/{}.conf'.format(script, PROJECT_NAME))
    sudo('a2ensite {}.conf'.format(PROJECT_NAME))

# 프로젝트 폴더 및 아파치 연동된 부분에 관련하여 권한 조정
# 리눅스 상에서 누구나 파일/디렉토리 상에서 권한을 액세스 할 수 있게(수정 포함) 조정
# chmod 777 파일 
def _grant_apache2():
    # 디렉토리 및 이하 파일 전부 포함 -> -R 로 표현
    # 이 디렉토리(이하 파일까지)의 주인은
    sudo('chown -R :www-data ~/{}'.format(PROJECT_NAME))
    # 이 파일의 권한 조정
    sudo('chmod -R 775 ~/{}'.format(PROJECT_NAME))

# 아파치 서버의 재가동
def _restart_apache2():
    # 루트 권한으로 아파치 서버를 재가동하시오.
    sudo('sudo service apache2 restart')


# 크게 흐름만 이해

# 절차 요약
"""
######################################################################################################################################################
1. git 생성
2. 개발
3. 개발한 코드를 git에 연동 -> git에 최신소스 반영
4. 최초 세팅 및 배포하는 경우, fab new_server
5. 추가 개발 이후 git에 반영, fab deploy를 통해서 서버에 최신 버전을 반영, 오픈 -> loop
######################################################################################################################################################
"""