from pathlib import Path

import os

import dj_database_url
import django_heroku
import environ

from decouple import config

# ENVIRONMENT VARIABLES
env = environ.Env(
    DEBUG=(bool, False)
)
environ.Env.read_env()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "23%/+|~`?^{}(!\><,.bb#kx9i^3$&n+z93#$fs=^6g*cw=cq*fxtn9or5wak4dbcyl*)"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'stormwealthinvestment.herokuapp.com', 'stormwealthinvestment.com', 'www.stormwealthinvestment.com']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # OWN APPS
    'apexapp.apps.ApexappConfig',
    'account.apps.AccountConfig',

    # THIRD PARTY APPS
    'widget_tweaks',
    'embed_video',

    # TAWK TO LIVE MESSAGING
    # 'tawkto',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # ADDING WHITENOISE AND COMMON MIDDLE WARE
    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',

    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'apextraders.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, "templates")
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'apextraders.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases
if DEBUG:
    DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }

    # HEROKU POSTGRES SETUP
    db_from_env = dj_database_url.config(conn_max_age=600)
    DATABASES['default'].update(db_from_env)

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/


STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'assets')
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)
# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# SITE ADMINS
ADMINS = (('daniel', 'ikegbunamdaniela1@gmail.com'),)


#  EMAIL CONFIGURATION
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.zoho.com'
EMAIL_PORT = 465
EMAIL_HOST_USER = "support@stormwealthinvestment.com"
EMAIL_HOST_PASSWORD = "Command22__"
DEFAULT_FROM_EMAIL = "support@stormwealthinvestment.com"
SERVER_EMAIL = "support@stormwealthinvestment.com"
EMAIL_USE_TLS = False
EMAIL_USE_SSL = True


if not DEBUG:
    # HTTPs Settings
    SESSION_COOKIE_SECURE = True
    # DJANGO SESSION SETTINGS 
    SESSION_SAVE_EVERY_REQUEST = True
    CSRF_COOKIE_SECURE = True
    # SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    # HSTS Settings
    SECURE_HSTS_SECONDS = 31536000  # A year
    SECURE_HSTS_PRELOAD = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True


# LOGIN URLS AND REDIRECTIONS
LOGIN_URL ="userdashboard:login"
LOGIN_REDIRECT_URL = "userdashboard:login"
LOGOUT_REDIRECT_URL = "userdashboard:login"

django_heroku.settings(locals())
