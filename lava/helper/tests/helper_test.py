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
A test helper class.

Here we define a general test class and its own setUp and tearDown methods that
all other test classes can inherit from.
"""

import os
import shutil
import sys
import tempfile

from unittest import TestCase
from mock import MagicMock


class HelperTest(TestCase):
    """Helper test class that all tests under the lava package can inherit."""
    def setUp(self):
        self.original_stdout = sys.stdout
        sys.stdout = open("/dev/null", "w")
        self.original_stderr = sys.stderr
        sys.stderr = open("/dev/null", "w")
        self.original_stdin = sys.stdin

        self.device = "a_fake_panda02"

        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.tempdir = tempfile.mkdtemp()
        self.parser = MagicMock()
        self.args = MagicMock()
        self.args.interactive = MagicMock(return_value=False)
        self.args.DEVICE = self.device

        self.config = MagicMock()
        self.config.get = MagicMock(return_value=self.tempdir)

    def tearDown(self):
        sys.stdin = self.original_stdin
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        shutil.rmtree(self.tempdir)
        os.unlink(self.temp_file.name)
