# Copyright (C) 2013 Linaro Limited
#
# Author: Milo Casagrande <milo.casagrande@linaro.org>
#
# This file is part of lava-tool.
#
# lava-tool is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# as published by the Free Software Foundation
#
# lava-tool is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with lava-tool.  If not, see <http://www.gnu.org/licenses/>.

"""
Commands class unit tests.
"""

import os
import shutil
import sys
import tempfile

from mock import MagicMock
from unittest import TestCase

from lava.device.commands import (
    BaseCommand,
    add,
    config,
    remove,
)

from lava.tool.errors import CommandError


class CommandsTest(TestCase):
    def setUp(self):
        # Fake the stdout.
        self.original_stdout = sys.stdout
        sys.stdout = open("/dev/null", "w")
        self.original_stderr = sys.stderr
        sys.stderr = open("/dev/null", "w")

        self.device = "panda02"

        self.tempdir = tempfile.mkdtemp()
        self.parser = MagicMock()
        self.args = MagicMock()
        self.args.interactive = MagicMock(return_value=False)
        self.args.DEVICE = self.device

        self.config = MagicMock()
        self.config.get = MagicMock(return_value=self.tempdir)

    def tearDown(self):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        shutil.rmtree(self.tempdir)

    def test_get_devices_path_0(self):
        # Tests that the correct devices path is returned.
        # This test returns a tempdir.
        base_command = BaseCommand(self.parser, self.args)
        base_command.config = self.config
        BaseCommand._create_devices_path = MagicMock()
        BaseCommand._get_dispatcher_paths = MagicMock(return_value=[
            self.tempdir])
        obtained = base_command._get_devices_path()
        expected_path = os.path.join(self.tempdir, "devices")
        self.assertEqual(expected_path, obtained)

    def test_get_devices_path_1(self):
        # Tests that the correct devices path is returned.
        # This test checks the user .config path is returned.
        base_command = BaseCommand(self.parser, self.args)
        base_command.config = self.config
        BaseCommand._create_devices_path = MagicMock()
        BaseCommand._get_dispatcher_paths = MagicMock(return_value=[])
        obtained = base_command._get_devices_path()
        expected_path = os.path.join(os.path.expanduser("~"), ".config",
                                     "lava-dispatcher", "devices")
        self.assertEqual(expected_path, obtained)

    def test_create_devices_path(self):
        # Tests that the correct devices path is created on the file system.
        base_command = BaseCommand(self.parser, self.args)
        base_command.config = self.config
        BaseCommand._get_dispatcher_paths = MagicMock(return_value=[
            self.tempdir])
        base_command._get_devices_path()
        expected_path = os.path.join(self.tempdir, "devices")
        self.assertTrue(os.path.isdir(expected_path))

    def test_add_invoke(self):
        # Tests invocation of the add command. Verifies that the conf file is
        # written to disk.
        add_command = add(self.parser, self.args)
        add_command.edit_config_file = MagicMock()
        add_command._get_devices_path = MagicMock(return_value=self.tempdir)
        add_command.invoke()

        expected_path = os.path.join(self.tempdir,
                                     ".".join([self.device, "conf"]))
        self.assertTrue(os.path.isfile(expected_path))

    def test_remove_invoke(self):
        # Tests invocation of the remove command. Verifies that the conf file
        # has been correctly removed.
        add_command = add(self.parser, self.args)
        add_command.edit_config_file = MagicMock()
        add_command._get_devices_path = MagicMock(return_value=self.tempdir)
        add_command.invoke()

        remove_command = remove(self.parser, self.args)
        remove_command._get_devices_path = MagicMock(return_value=self.tempdir)
        remove_command.invoke()

        expected_path = os.path.join(self.tempdir,
                                     ".".join([self.device, "conf"]))
        self.assertFalse(os.path.isfile(expected_path))

    def test_remove_invoke_raises(self):
        # Tests invocation of the remove command, with a non existent device
        # configuration file.
        remove_command = remove(self.parser, self.args)
        remove_command._get_devices_path = MagicMock(return_value=self.tempdir)

        self.assertRaises(CommandError, remove_command.invoke)

    def test_config_invoke_raises(self):
        # Tests invocation of the config command, with a non existent device
        # configuration file.
        config_command = config(self.parser, self.args)
        config_command._get_devices_path = MagicMock(return_value=self.tempdir)

        self.assertRaises(CommandError, config_command.invoke)
