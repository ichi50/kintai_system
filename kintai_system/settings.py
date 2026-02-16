#kintai_system/setting.py
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-e6h1k$0^*e-9uxf7iakn%1lr9f#$0s9&2_w(x1hp+e$svgzrwb'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    '*', # EC2パブリックIP (本番用)
    '127.0.0.1',     # ローカルループバックIP (開発用) ★★★ これを追加 ★★★
    'localhost',     # ローカルホスト名 (開発用) ★★★ これも追加 ★★★
    'kintai.mydns.jp'
]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    #'django_otp',
    #'django_otp.plugins.otp_totp',
    #'two_factor',
    'widget_tweaks',
    'common',
    'schedule_app',
    'scheduling_app',
    'achieve_app',
    'correction_app',
    'admin_app',
    'admin_scheduling_app',
    'admin_correction_app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'kintai_system.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'attendance' / 'templates'], # ★★★ この行を追加 ★★★
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'kintai_system.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'kintai',
        'USER': 'ichi50',
        'PASSWORD': os.environ.get('DB_PASSWORD', '1234'),
        'HOST': os.environ.get('DB_HOST','127.0.0.1'), 
        'PORT': os.environ.get('DB_PORT', '3306'), 
        'OPTIONS': {
            'charset': 'utf8mb4',
        }
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'ja'

TIME_ZONE = 'Asia/Tokyo'

USE_I18N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/accounts/login/'
# ログイン後のリダイレクト先URLを定義
# ルートパス（'/'）にリダイレクトする
LOGIN_REDIRECT_URL = '/'

# ログアウト後のリダイレクト先URLもついでに定義
LOGOUT_REDIRECT_URL = '/accounts/login/'

# settings.py の最下部などに追加
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

AUTHENTICATION_BACKENDS = [
    # OTP認証バックエンド: OTPをチェックするロジック
    #'django_otp.backends.OTPAuthenticationBackend',
    # カスタム認証バックエンドを設定
    'kintai_system.auth_backends.EmployeeIdOrEmailBackend',
    # 念のため、標準の認証バックエンドも残すか（必要に応じて削除）
    #'django.contrib.auth.backends.ModelBackend',
]

#TWO_FACTOR_ENABLED_METHODS = [
#    'email',  # メールによるOTPを許可・推奨
    # 'generator', # TOTP (Google Authenticator) を許可する場合
#]
