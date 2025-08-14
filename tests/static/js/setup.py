#!/usr/bin/env python3
"""
Setup script for VoiceClone Pro
Advanced Voice Cloning & Text-to-Speech Platform
"""

from setuptools import setup, find_packages
import os
import sys

# Ensure minimum Python version
if sys.version_info < (3, 8):
    sys.exit('Python 3.8 or later is required')

# Read version from file
def get_version():
    version_file = os.path.join(os.path.dirname(__file__), 'VERSION')
    if os.path.exists(version_file):
        with open(version_file, 'r') as f:
            return f.read().strip()
    return '1.0.0'

# Read long description from README
def get_long_description():
    readme_file = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_file):
        with open(readme_file, 'r', encoding='utf-8') as f:
            return f.read()
    return 'Advanced Voice Cloning & Text-to-Speech Platform'

# Read requirements from file
def get_requirements():
    requirements_file = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(requirements_file):
        with open(requirements_file, 'r') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

# Development requirements
dev_requirements = [
    'pytest>=7.4.0',
    'pytest-cov>=4.1.0',
    'pytest-flask>=1.2.0',
    'pytest-watch>=4.2.0',
    'black>=23.7.0',
    'flake8>=6.0.0',
    'isort>=5.12.0',
    'mypy>=1.5.0',
    'pre-commit>=3.3.0',
    'sphinx>=7.1.0',
    'sphinx-rtd-theme>=1.3.0',
]

# Production requirements
prod_requirements = [
    'gunicorn>=21.2.0',
    'uvicorn>=0.23.0',
    'nginx>=1.25.0',
    'supervisor>=4.2.0',
]

# Audio processing requirements
audio_requirements = [
    'librosa>=0.10.1',
    'soundfile>=0.12.1',
    'pydub>=0.25.1',
    'pyaudio>=0.2.11',
    'mutagen>=1.47.0',
]

# Machine learning requirements
ml_requirements = [
    'torch>=2.0.0',
    'torchaudio>=2.0.0',
    'transformers>=4.30.0',
    'datasets>=2.14.0',
    'accelerate>=0.21.0',
]

# Cloud provider requirements
cloud_requirements = [
    'boto3>=1.28.0',
    'azure-cognitiveservices-speech>=1.30.0',
    'google-cloud-texttospeech>=2.14.0',
]

setup(
    name='voiceclone-pro',
    version=get_version(),
    description='Advanced Voice Cloning & Text-to-Speech Platform',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    author='VoiceClone Pro Team',
    author_email='team@voiceclonepro.com',
    url='https://github.com/yourusername/voiceclone-pro',
    project_urls={
        'Documentation': 'https://voiceclonepro.readthedocs.io/',
        'Source': 'https://github.com/yourusername/voiceclone-pro',
        'Tracker': 'https://github.com/yourusername/voiceclone-pro/issues',
    },
    packages=find_packages(exclude=['tests*', 'docs*']),
    include_package_data=True,
    package_data={
        'voiceclone': [
            'static/**/*',
            'templates/**/*',
            'models/**/*',
        ],
    },
    install_requires=get_requirements(),
    extras_require={
        'dev': dev_requirements,
        'prod': prod_requirements,
        'audio': audio_requirements,
        'ml': ml_requirements,
        'cloud': cloud_requirements,
        'all': dev_requirements + prod_requirements + audio_requirements + ml_requirements + cloud_requirements,
    },
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Multimedia :: Sound/Audio :: Speech',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Framework :: Flask',
    ],
    keywords=[
        'voice-cloning',
        'text-to-speech',
        'tts',
        'speech-synthesis',
        'ai',
        'machine-learning',
        'audio-processing',
        'nlp',
        'voice-ai',
        'flask',
        'web-application',
    ],
    entry_points={
        'console_scripts': [
            'voiceclone=app:main',
            'voiceclone-server=app:run_server',
            'voiceclone-worker=celery_worker:main',
            'voiceclone-setup=scripts.setup:main',
        ],
    },
    zip_safe=False,
    platforms=['any'],
    license='MIT',
    
    # Additional metadata
    maintainer='VoiceClone Pro Team',
    maintainer_email='maintainer@voiceclonepro.com',
    download_url='https://github.com/yourusername/voiceclone-pro/archive/v{}.tar.gz'.format(get_version()),
    
    # Development status
    options={
        'build_scripts': {
            'executable': '/usr/bin/env python3',
        },
    },
    
    # Testing configuration
    test_suite='tests',
    tests_require=[
        'pytest>=7.4.0',
        'pytest-cov>=4.1.0',
        'pytest-flask>=1.2.0',
    ],
    
    # Command class for custom commands
    cmdclass={},
)

# Post-installation message
def post_install_message():
    print("""
    ╔══════════════════════════════════════════════╗
    ║           VoiceClone Pro Installed!          ║
    ╠══════════════════════════════════════════════╣
    ║                                              ║
    ║  🎉 Installation completed successfully!     ║
    ║                                              ║
    ║  Quick Start:                                ║
    ║    voiceclone-setup                          ║
    ║    voiceclone-server                         ║
    ║                                              ║
    ║  Or using Python:                            ║
    ║    python app.py                             ║
    ║                                              ║
    ║  Visit: http://localhost:5000                ║
    ║                                              ║
    ║  Documentation:                              ║
    ║    https://voiceclonepro.readthedocs.io/     ║
    ║                                              ║
    ║  Support:                                    ║
    ║    https://github.com/yourusername/          ║
    ║    voiceclone-pro/issues                     ║
    ║                                              ║
    ╚══════════════════════════════════════════════╝
    """)

if __name__ == '__main__':
    # Run setup
    setup()
    
    # Show post-installation message
    if 'install' in sys.argv:
        post_install_message()
