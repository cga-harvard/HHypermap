import os
from distutils.core import setup
from distutils.command.install import INSTALL_SCHEMES
from setuptools import find_packages
from hypermap import __version__, __description__


def read(*rnames):
    with open(os.path.join(os.path.dirname(__file__), *rnames)) as ff:
        return ff.read()


setup(
    name=__description__,
    version=__version__,
    author='',
    author_email='',
    url='https://github.com/cga-harvard/HHypermap',
    download_url='https://github.com/cga-harvard/HHypermap',
    description='Django Registry by Harvard CGA',
    long_description=(read('README.md')),
    classifiers=[
        'Development Status :: 1 - Planning',
    ],
    license="BSD",
    keywords="hypermap django",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'amqplib',
        'arcrest',
        'celery',
        'Django>=1.8, <1.12',
        'django-debug-toolbar',
        'django-pagination',
        'django-taggit',
        'django-extensions',
        'dj-database-url',
        'django-cache-url',
        'django-basic-authentication-decorator',
        'elasticsearch',
        'pika',
        'pycsw>=2.0.2',
        'flake8',
        'httmock',
        'djmp>=0.2.10',
        'MapProxy>=1.9',
        'djangorestframework',
        'django-celery',
        'isodate',
        'nose',
        'OWSLib',
        'Paver',
        'Pillow',
        'python-memcached',
        'psycopg2',
        'pysolr',
        'requests',
        'webtest',
    ]
)
