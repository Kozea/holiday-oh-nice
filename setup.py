from setuptools import find_packages, setup

tests_requirements = [
    'pytest',
    'pytest-cov',
    'pytest-flake8',
    'pytest-isort',
]

setup(
    name="holiday-oh-nice",
    version="0.1.dev0",
    description="Oh nice!",
    url="https://holiday.kozea.fr",
    author="Kozea",
    packages=find_packages(),
    include_package_data=True,
    scripts=['holiday.py'],
    install_requires=[
        'Flask',
        'Flask-SQLAlchemy',
        'httplib2',
        'oauth2client',
    ],
    tests_require=tests_requirements,
    extras_require={'test': tests_requirements}
)
