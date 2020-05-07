import pytest
from server import DEFAULT_PORT


def pytest_addoption(parser):
    parser.addoption(
        "--server", action="store", default="localhost:{0}".format(DEFAULT_PORT), help="the ip:port of the rpyc server"
    )


@pytest.fixture(scope='session')
def server_ip_port(request):
    return request.config.getoption("--server")
