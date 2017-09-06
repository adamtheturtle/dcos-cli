import json
import os

import pytest

from dcos import config, constants, util

from .helpers.common import assert_command, exec_command


@pytest.fixture(scope="module")
def acs_token():
    return config.get_config().get('core.dcos_acs_token')


@pytest.fixture
def temp_dcos_dir():
    with util.tempdir() as tempdir:
        old_dcos_dir = os.environ.get(constants.DCOS_DIR_ENV)
        try:
            os.environ[constants.DCOS_DIR_ENV] = tempdir
            yield tempdir
        finally:
            if old_dcos_dir is None:
                os.environ.pop(constants.DCOS_DIR_ENV)
            else:
                os.environ[constants.DCOS_DIR_ENV] = old_dcos_dir


def test_migration_with_acs_token(acs_token, temp_dcos_dir):
    _copy_config_to_dcos_dir('dcos.toml')

    config.set_val('core.dcos_acs_token', acs_token)

    returncode, stdout, _ = exec_command(['dcos', 'cluster', 'list', '--json'])
    assert returncode == 0

    cluster_list = json.loads(stdout.decode('utf-8'))
    assert len(cluster_list) == 1
    assert cluster_list[0]['url'] == "http://dcos.snakeoil.mesosphere.com"


def test_migration_without_acs_token(acs_token, temp_dcos_dir):
    _copy_config_to_dcos_dir('dcos.toml')

    stderr = (
        b"No clusters are currently configured. "
        b"To configure one, run `dcos cluster setup <dcos_url>`\n"
    )

    # Without an ACS token, the migration shouldn't occur
    assert_command(['dcos', 'cluster', 'list'], returncode=1, stderr=stderr)


def _copy_config_to_dcos_dir(name):
    """
    :param name: name of the config fixture to copy.
    :type name: str
    """

    deprecated_config = os.path.join(
        os.path.dirname(__file__),
        '../data/cluster_migration/{}'.format(name))

    # make sure the config has the proper permission
    os.chmod(deprecated_config, 0o600)

    dst = os.path.join(os.environ.get(constants.DCOS_DIR_ENV), 'dcos.toml')

    util.sh_copy(deprecated_config, dst)
