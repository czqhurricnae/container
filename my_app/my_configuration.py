""""
app.config.from_object('my_configuration.BaseConfig')
must be in the same level of  instance 'app' package
"""


class BaseConfig(object):
    """
    Base config class
    """
    SECRET_KEY = 'hard to guess'
    DEBUG = True