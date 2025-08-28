from pathlib import Path
import os
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING
SECRET_KEY = 'django-insecure-hmgz@z)+q&!s0ej+94lq51^5in%ood-=qfs8155qwx5(y5w%&-'
DEBUG = True

ALLOWED_HOSTS = ['*']
# settings.py
# ---- LOGIN/LOGOUT redirect ----
LOGIN_REDIRECT_URL = "/"        # login ke baad landing page
LOGOUT_REDIRECT_URL = "/"       # logout ke baad landing page
ACCOUNT_LOGOUT_REDIRECT_URL = "/"   # allauth logout redirect

LOGIN_URL = '/accounts/google/login/'   # force login = google login
LOGIN_REDIRECT_URL = '/'                # login ke baad redirect
LOGOUT_REDIRECT_URL = '/'               # logout ke baad redirect

ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False

SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_QUERY_EMAIL = True
SOCIALACCOUNT_STORE_TOKENS = True

RAZORPAY_KEY_ID = "rzp_live_RAc1wpiDhkienh"
RAZORPAY_KEY_SECRET = "CHYJZyFtP5Sy1FWx22nJSrIv"




INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # my apps
    'accounts',
    'feed',
    'payment',
    # all-auth apps
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
]

SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",  # default
    "allauth.account.auth_backends.AuthenticationBackend",  # allauth
]

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": "64761230761-6lk00bclccucj01hlnt1c920qmlheqjc.apps.googleusercontent.com",
            "secret": "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",
            "key": ""
        }
    }
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
        "allauth.account.middleware.AccountMiddleware",
]

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

ROOT_URLCONF = 'my_pay.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        "DIRS": [BASE_DIR / "templates"], 
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

WSGI_APPLICATION = 'my_pay.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'neondb',   # 👈 yaha pe my_pay ki jagah neondb likho
        'USER': 'neondb_owner',
        'PASSWORD': 'npg_DFOBxaXCof89',
        'HOST': 'ep-purple-morning-ad11ohkv-pooler.c-2.us-east-1.aws.neon.tech',
        'PORT': '5432',
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}




# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
