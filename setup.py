from setuptools import setup, find_packages
install_requires = [
    'delegator.py',
    'docker',
    'requests'
]

tests_require = [
    'nose',
]

setup(
    name='fabric-testing',
    version="0.1.0",
    description='Python Fabric Testing',
    #long_description=long_description,
    author='stephane.rault@radicalspam.org',
    url='https://git.lbn.fr/srault95/python-fabric-testing',
    packages=['fabric_testing'],
    #include_package_data=True, 
    test_suite='nose.collector',
    tests_require=[
        'nose',
    ],
    install_requires=install_requires,
    extras_require={
        'testing': install_requires + tests_require
    },
)
