from distutils.core import setup

setup(
    name='FHLB',
    version='0.1.0',
    author='Mark C. Woodworth',
    author_email='markcwoodworth@gmail.com',
    packages=[],
    scripts=[],
    url='http://pypi.python.org/pypi/FHLB/',
    license='MIT.txt',
    description='API Interface to Federal Home Loan Bank of San Francisco.',
    long_description=open('README.md').read(),
    install_requires=[
        "selenium",
        "lxml",
        "python-dateutil"
    ],
)