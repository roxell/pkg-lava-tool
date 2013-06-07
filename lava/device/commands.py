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

import os
import subprocess
import sys

from lava.config import InteractiveConfig, Parameter
from lava.device import get_known_device
from lava.tool.command import Command, CommandGroup
from lava.tool.utils import has_command


# Default lava-dispatcher path, has to be joined with an instance full path.
DEFAUL_DISPATCHER_PATH = os.path.join('etc', 'lava-dispatcher')
# Default devices path.
DEFAULT_DEVICES_PATH = 'devices'
DEVICE_FILE_SUFFIX = "conf"


class device(CommandGroup):
    """LAVA devices handling"""

    namespace = "lava.device.commands"


class BaseCommand(Command):
    def __init__(self, parser, args):
        super(BaseCommand, self).__init__(parser, args)
        self.config = InteractiveConfig(force_interactive=self.args.interactive)

    @classmethod
    def register_arguments(cls, parser):
        super(BaseCommand, cls).register_arguments(parser)
        parser.add_argument("-i", "--interactive",
                            action='store_true',
                            help=("Forces asking for input parameters even if "
                                  "we already have them cached."))

    def _get_devices_path(self):
        """Gets the path to the devices in the LAVA dispatcher."""
        dispatcher_path = self.config.get(Parameter("lava_dispatcher"))
        if not dispatcher_path:
            # Nothing provided? We write on the current dir.
            dispatcher_path = os.path.join(os.getcwd(), DEFAUL_DISPATCHER_PATH)
            print "LAVA dispatcher path will be: %s" % dispatcher_path

        devices_path = os.path.join(dispatcher_path, DEFAULT_DEVICES_PATH)
        return devices_path

    def edit_config_file(file):
        """Opens the specified file with the default file editor.

        :param file: The file to edit."""
        # TODO: find a better way
        editors = []
        editors.append(os.environ.get("EDITOR", None))
        if has_command('sensible-editor'):
            editors.append("sensible-editor")
        if has_command('xdg-open'):
            editors.append('xdg-open')

        try:
            editor = editors.pop(0)
            subprocess.Popen(editor).wait()
        except Exception:
            pass


class add(BaseCommand):
    """Implements 'lava device add' command."""

    @classmethod
    def register_arguments(cls, parser):
        super(add, cls).register_arguments(parser)
        parser.add_argument("DEVICE", help="The name of the device to add.")

    def invoke(self):
        devices_path = self._get_devices_path()
        real_file_name = ".".join(self.args.DEVICE, DEVICE_FILE_SUFFIX)
        device_conf_file = os.path.abspath(os.path.join(devices_path,
                                                        real_file_name))

        if os.path.exists(device_conf_file):
            print ("A device configuration file named '%s' already exists."
                   % real_file_name)
            print "Use 'lava config DEVICE' to edit it."
            sys.exit(-1)

        device = get_known_device(self.args.DEVICE)
        device.write(device_conf_file)

        print ("Created device file '%s' in: " %
               (self.args.DEVICE, devices_path))

        self.edit_config_file(device_conf_file)


class remove(BaseCommand):
    """Implements 'lava device remove' command."""

    @classmethod
    def register_arguments(cls, parser):
        super(remove, cls).register_arguments(parser)
        parser.add_argument("DEVICE",
                            help="The name of the device to remove.")

    def invoke(self):
        devices_path = self._get_devices_path()
        real_file_name = ".".join(self.args.DEVICE, DEVICE_FILE_SUFFIX)
        device_conf = os.path.join(devices_path, real_file_name)
        if os.path.isfile(device_conf):
            os.remove(device_conf)
            print "Device configuration file %s removed." % self.args.DEVICE
        else:
            print ("Cannot remove file '%s' at: %s. It does not exist or it "
                   "is not a file." % (real_file_name, devices_path))


class config(BaseCommand):
    """Implements 'lava device config DEVICE' command."""
    @classmethod
    def register_arguments(cls, parser):
        super(config, cls).register_arguments(parser)
        parser.add_argument("DEVICE",
                            help="The name of the device to edit.")

    def invoke(self):
        devices_path = self._get_devices_path()
        real_file_name = ".".join(self.args.DEVICE, DEVICE_FILE_SUFFIX)
        device_conf = os.path.join(devices_path, real_file_name)
        if os.path.isfile(device_conf):
            self.edit_config_file(device_conf)
        else:
            print ("Cannot edit file '%s' at: %s. It does not exist or it "
                   "is not a file." % (real_file_name, devices_path))
