import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--server", action="store", default="localhost:18871", help="the ip:port of the rpyc server"
    )


@pytest.fixture(scope='session')
def server_ip_port(request):
    return request.config.getoption("--server")
