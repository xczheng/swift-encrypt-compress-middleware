from setuptools import setup

setup(name='myswift',
    packages=['myswift', ],
    zip_safe=False,
    entry_points={
        'paste.filter_factory': ['compress = myswift.compress:filter_factory', 'encrypt = myswift.encrypt:filter_factory'],
    },
)
