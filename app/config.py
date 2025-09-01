# 앱의 주요 설정 저장용
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev_secret_key_for_prototyping'
    DEBUG = False
    TESTING = False
    # 여기에 다른 전역 설정을 추가

class DevelopmentConfig(Config):
    DEBUG = True
    # 여기에 개발 환경별 설정을 추가

class ProductionConfig(Config):
    # 여기에 프로덕션 환경별 설정을 추가
    pass

# app/__init__.py에서 다음과 같이 사용할 수 있음
# app.config.from_object('app.config.DevelopmentConfig')
# 또는 __init__.py에 직접 값을 넣는다면, 이 파일은 기본적인 설정에는 덜 중요할 수 있음