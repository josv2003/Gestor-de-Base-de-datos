from setuptools import setup
import os

APP = ['app.py']
DATA_FILES = [
    ('templates', ['templates/'+ f for f in os.listdir('templates')]),
    ('static', ['static/'+ f for f in os.listdir('static')])
]
OPTIONS = {
    'argv_emulation': False,
    'packages': ['flask', 'flask_login', 'flask_session', 'pandas', 'pyodbc', 'zlib'],
    'excludes': ['tkinter'],
    'plist': {
        'CFBundleName': 'GestorDB',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleIdentifier': 'com.idea.gestordb',
    },
    'skip_archive': True,
    'zipfile': None,
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app']
)