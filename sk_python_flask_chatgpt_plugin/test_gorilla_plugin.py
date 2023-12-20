"""
Tests for GorillaPlugin class.

This file contains test cases for the GorillaPlugin class to ensure it properly handles setting
the working directory, collecting environment information, and implementing utility
functions necessary for the Gorilla CLI plugin functionality.
"""
from unittest import mock

import pytest
from gorilla_plugin import GorillaPlugin


def test_set_working_directory():
    gorilla_plugin = GorillaPlugin()
    gorilla_plugin.set_working_directory('/test/directory')
    assert gorilla_plugin._working_directory == '/test/directory'

def test_collect_environment_info():
    """
    Test collecting the environment information within the working directory.

    Mocks the os.walk function to simulate the file structure and asserts the collected environment information is stored correctly.
    """
    gorilla_plugin = GorillaPlugin()
    gorilla_plugin._working_directory = '/test/directory'
    with mock.patch('os.walk') as mocked_walk:
        mocked_walk.return_value = [('/test/directory', ['subdir'], ['file1', 'file2'])]
        gorilla_plugin.collect_environment_info()
    assert gorilla_plugin._env_info == {'/test/directory': ['subdir', 'file1', 'file2']}

def test_compare_environment_info():
    gorilla_plugin = GorillaPlugin()
    initial_env_info = {'/test/directory': ['subdir', 'file1', 'file2']}
    updated_env_info = {'/test/directory': ['subdir', 'file1', 'file3']}
    differences = gorilla_plugin.compare_environment_info(initial_env_info, updated_env_info)
    assert differences == {'/test/directory': {'initial': ['subdir', 'file1', 'file2'], 'updated': ['subdir', 'file1', 'file3']}}

def test_queue_commands():
    gorilla_plugin = GorillaPlugin()
    gorilla_plugin._cli_path = '/test/cli/path'
    with mock.patch('subprocess.Popen') as mocked_popen:
        mocked_popen.return_value.communicate.return_value = (b'test command', b'')
        mocked_popen.return_value.returncode = 0
        result = gorilla_plugin.queue_commands(['test natural language command'])
    assert result == {'queued_commands': ['test command'], 'environment_info': {}}

def test_dump_commands_to_script():
    gorilla_plugin = GorillaPlugin()
    with mock.patch('builtins.open', new_callable=mock.mock_open) as mocked_open:
        gorilla_plugin.dump_commands_to_script(['test command1', 'test command2'], 'test_filename')
    mocked_open.assert_called_once_with('test_filename.sh', 'w')

def test_execute_commands():
    gorilla_plugin = GorillaPlugin()
    with mock.patch('subprocess.Popen') as mocked_popen, mock.patch('builtins.input', return_value='yes'):
        mocked_popen.return_value.communicate.return_value = (b'test output', b'')
        mocked_popen.return_value.returncode = 0
        gorilla_plugin.execute_commands(['test command'])
