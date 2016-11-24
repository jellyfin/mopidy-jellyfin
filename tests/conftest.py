import pytest


@pytest.fixture
def config():
    return {
        'emby': {
            'hostname': 'https://foo.bar',
            'port': 443,
            'username': 'embyuser',
            'password': 'embypassword'
        },
        'proxy': {
            'foo': 'bar'
        }
    }
