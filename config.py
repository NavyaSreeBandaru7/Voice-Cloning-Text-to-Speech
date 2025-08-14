"""
Configuration settings for VoiceClone Pro
"""

import os
from datetime import timedelta
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.absolute()

class Config:
    """Base configuration class"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = False
    TESTING = False
    
    # File upload settings
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    UPLOAD_FOLDER = BASE_DIR / 'uploads'
    OUTPUT_FOLDER = BASE_DIR / 'outputs'
    TEMP_FOLDER = BASE_DIR / 'temp'
    
    # Audio processing settings
    ALLOWED_EXTENSIONS = {'wav', 'mp3', 'ogg', 'm4a', 'flac', 'aac'}
    MAX_AUDIO_DURATION = 300  # 5 minutes maximum
    MIN_AUDIO_DURATION = 5    # 5 seconds minimum
    DEFAULT_SAMPLE_RATE = 44100
    
    # Voice cloning settings
    VOICE_CLONE_QUALITIES = ['draft', 'standard', 'high', 'premium']
    SUPPORTED_LANGUAGES = [
        'en-US', 'en-GB', 'es-ES', 'fr-FR', 'de-DE',
        'it-IT', 'pt-BR', 'zh-CN', 'ja-JP', 'ko-KR'
    ]
    
    # TTS settings
    TTS_ENGINES = ['gtts', 'pyttsx3', 'azure', 'aws']
    DEFAULT_TTS_ENGINE = 'gtts'
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE = 60
    RATE_LIMIT_PER_HOUR = 1000
    
    # Job settings
    JOB_TIMEOUT = 3600  # 1 hour
    CLEANUP_INTERVAL = 3600  # 1 hour
    MAX_CONCURRENT_JOBS = 10
    
    # Database settings (for production)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{BASE_DIR}/voiceclone.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_timeout': 20,
        'pool_recycle': -1,
        'pool_pre_ping': True
    }
    
    # Redis settings (for caching and job queue)
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # External API settings
    AZURE_SPEECH_KEY = os.environ.get('AZURE_SPEECH_KEY')
    AZURE_SPEECH_REGION = os.environ.get('AZURE_SPEECH_REGION')
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
    
    # Security settings
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # CORS settings
    CORS_ORIGINS = [
        'http://localhost:3000',
        'http://localhost:8000',
        'https://yourdomain.com'
    ]
    
    # Logging settings
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Performance settings
    ENABLE_THREADING = True
    THREADED = True
    PROCESSES = 1
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration"""
        # Create necessary directories
        for folder in [Config.UPLOAD_FOLDER, Config.OUTPUT_FOLDER, Config.TEMP_FOLDER]:
            folder.mkdir(exist_ok=True)

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    
    # Development database
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{BASE_DIR}/voiceclone_dev.db'
    
    # Relaxed rate limiting for development
    RATE_LIMIT_PER_MINUTE = 1000
    RATE_LIMIT_PER_HOUR = 10000

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    
    # In-memory database for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Test folders
    UPLOAD_FOLDER = BASE_DIR / 'test_uploads'
    OUTPUT_FOLDER = BASE_DIR / 'test_outputs'
    TEMP_FOLDER = BASE_DIR / 'test_temp'
    
    # Disable rate limiting for tests
    RATE_LIMIT_PER_MINUTE = 10000
    RATE_LIMIT_PER_HOUR = 100000

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    
    # Use environment variables for sensitive settings
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # Production database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # Strict rate limiting
    RATE_LIMIT_PER_MINUTE = 30
    RATE_LIMIT_PER_HOUR = 500
    
    # Production folders
    UPLOAD_FOLDER = Path('/var/www/voiceclone/uploads')
    OUTPUT_FOLDER = Path('/var/www/voiceclone/outputs')
    TEMP_FOLDER = Path('/var/www/voiceclone/temp')
    
    # Enhanced security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Production-specific initialization
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not app.debug and not app.testing:
            # File logging
            file_handler = RotatingFileHandler(
                'logs/voiceclone.log',
                maxBytes=10240000,
                backupCount=10
            )
            file_handler.setFormatter(logging.Formatter(cls.LOG_FORMAT))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            
            app.logger.setLevel(logging.INFO)
            app.logger.info('VoiceClone Pro startup')

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])
