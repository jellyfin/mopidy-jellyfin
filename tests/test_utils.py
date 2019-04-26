from __future__ import unicode_literals

from mock import Mock


from mopidy_jellyfin import utils


def test_decorator():
    func = Mock()
    decorated_func = utils.cache()
    decorated_func(func)
    func()

    assert func.called is True
    assert decorated_func._call_count == 1


def test_set_default_cache():

    @utils.cache()
    def returnstring():
        return 'ok'

    assert returnstring() == 'ok'


def test_set_ttl_cache():
    func = Mock()
    decorated_func = utils.cache(func, ttl=5)
    func()

    assert func.called is True
    assert decorated_func._call_count == 1
    assert decorated_func.ttl == 5
