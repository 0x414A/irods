import sys

if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest

import copy
import os
import time

from .. import test
from . import settings
from .resource_suite import ResourceBase
from ..controller import IrodsController
from ..configuration import IrodsConfig
from .. import lib
from . import session
from ..test.command import assert_command

SessionsMixin = session.make_sessions_mixin([('otherrods','pass')], [])


class TestControlPlane(SessionsMixin, unittest.TestCase):
    def test_pause_and_resume(self):
        assert_command('irods-grid pause --all', 'STDOUT_SINGLELINE', 'pausing')

        # need a time-out assert icommand for ils here

        assert_command('irods-grid resume --all', 'STDOUT_SINGLELINE', 'resuming')

        # Make sure server is actually responding
        assert_command('ils', 'STDOUT_SINGLELINE', IrodsConfig().client_environment['irods_zone_name'])
        assert_command('irods-grid status --all', 'STDOUT_SINGLELINE', 'hosts')

    def test_status(self):
        assert_command('irods-grid status --all', 'STDOUT_SINGLELINE', 'hosts')

    def test_hosts_separator(self):
        for s in [',', ', ']:
            hosts_string = s.join([lib.get_hostname()]*2)
            assert_command(['irods-grid', 'status', '--hosts', hosts_string], 'STDOUT_SINGLELINE', lib.get_hostname())

    @unittest.skipIf(test.settings.RUN_IN_TOPOLOGY, 'Skip for Topology Testing: No way to restart grid')
    def test_shutdown(self):
        assert lib.re_shm_exists()

        assert_command('irods-grid shutdown --all', 'STDOUT_SINGLELINE', 'shutting down')
        time.sleep(2)
        assert_command('ils', 'STDERR_SINGLELINE', 'USER_SOCK_CONNECT_ERR')

        assert not lib.re_shm_exists(), lib.re_shm_exists()

        IrodsController().start()

    def test_shutdown_local_server(self):
        initial_size_of_server_log = lib.get_file_size_by_path(IrodsConfig().server_log_path)
        assert_command(['irods-grid', 'shutdown', '--hosts', lib.get_hostname()], 'STDOUT_SINGLELINE', 'shutting down')
        time.sleep(10) # server gives control plane the all-clear before printing done message
        assert 1 == lib.count_occurrences_of_string_in_log(IrodsConfig().server_log_path, 'iRODS Server is done', initial_size_of_server_log)
        IrodsController().start()

    def test_invalid_client_environment(self):
        env_backup = copy.deepcopy(self.admin_sessions[0].environment_file_contents)

        if 'irods_server_control_plane_port' in self.admin_sessions[0].environment_file_contents:
            del self.admin_sessions[0].environment_file_contents['irods_server_control_plane_port']
        if 'irods_server_control_plane_key' in self.admin_sessions[0].environment_file_contents:
            del self.admin_sessions[0].environment_file_contents['irods_server_control_plane_key']
        if 'irods_server_control_plane_encryption_num_hash_rounds' in self.admin_sessions[0].environment_file_contents:
            del self.admin_sessions[0].environment_file_contents['irods_server_control_plane_encryption_num_hash_rounds']
        if 'irods_server_control_plane_port' in self.admin_sessions[0].environment_file_contents:
            del self.admin_sessions[0].environment_file_contents['irods_server_control_plane_encryption_algorithm']

        self.admin_sessions[0].assert_icommand('irods-grid status --all', 'STDERR_SINGLELINE', 'USER_INVALID_CLIENT_ENVIRONMENT')

        self.admin_sessions[0].environment_file_contents = env_backup
