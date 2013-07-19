# Copyright (C) 2013 Linaro Limited
#
# Author: Antonio Terceiro <antonio.terceiro@linaro.org>
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
LAVA job commands.
"""

import os
import sys
import xmlrpclib

from lava.helper.command import BaseCommand
from lava.helper.dispatcher import get_devices
from lava.helper.template import get_key
from lava.job import Job
from lava.job.templates import (
    LAVA_TEST_SHELL,
    TESTDEF_REPOS_TAR_REPO,
)
from lava.parameter import (
    ListParameter,
    Parameter,
    SingleChoiceParameter,
)
from lava.tool.command import CommandGroup
from lava.tool.errors import CommandError
from lava_tool.utils import has_command


# Name of the config value to store the job ids.
JOBS_ID = "jobs_id"
# Name of the config value to store the LAVA server URL.
SERVER = "server"
# Name of the config value to store the LAVA rpc_endpoint.
RPC_ENDPOINT = "rpc_endpoint"

# Default job file extension.
DEFAULT_EXTENSION = "json"
# Possible extension for a job file.
JOB_FILE_EXTENSIONS = [DEFAULT_EXTENSION]


class job(CommandGroup):
    """LAVA job file handling."""
    namespace = 'lava.job.commands'


class new(BaseCommand):
    """Creates a new job file."""

    @classmethod
    def register_arguments(cls, parser):
        super(new, cls).register_arguments(parser)
        parser.add_argument("FILE", help=("Job file to be created."))

    def invoke(self, tests_dir=None):
        full_path = os.path.abspath(self.args.FILE)
        job_file = self.verify_file_extension(full_path, DEFAULT_EXTENSION,
                                              JOB_FILE_EXTENSIONS)

        if os.path.exists(job_file):
            raise CommandError('{0} already exists.'.format(job_file))

        job_instance = Job(LAVA_TEST_SHELL)
        if tests_dir:
            testdef_tar_repo = get_key(job_instance.data,
                                      TESTDEF_REPOS_TAR_REPO)
            testdef_tar_repo.set(tests_dir)
            testdef_tar_repo.asked = True

        with open(job_file, 'w') as write_file:
            job_instance.fill_in(self.config)
            job_instance.write(write_file)


class submit(BaseCommand):
    """Submits the specified job file."""

    JOBS_ID = "jobs_id"

    @classmethod
    def register_arguments(cls, parser):
        super(submit, cls).register_arguments(parser)
        parser.add_argument("FILE", help=("The job file to submit."))

    def invoke(self):
        jobfile = self.args.FILE
        jobdata = open(jobfile, 'rb').read()

        server = self.authenticated_server()

        try:
            job_id = server.scheduler.submit_job(jobdata)
            print >> sys.stdout, "Job submitted with job ID {0}".format(job_id)

            # Store the job_id into the config file.
            if job_id:
                # We need first to take out the old values, and then store the
                # new one.
                job_ids_parameter = ListParameter(JOBS_ID)
                job_ids_parameter.asked = True

                value = self.config.get_from_backend(job_ids_parameter)
                if value:
                    job_ids_parameter.set(value)

                job_ids_parameter.add(job_id)
                self.config.put_parameter(job_ids_parameter)
        except xmlrpclib.Fault, exc:
            raise CommandError(str(exc))


class run(BaseCommand):
    """Runs the specified job file on the local dispatcher."""

    @classmethod
    def register_arguments(cls, parser):
        super(run, cls).register_arguments(parser)
        parser.add_argument("FILE", help=("The job file to submit."))

    def invoke(self):
        if os.path.isfile(self.args.FILE):
            if has_command("lava-dispatch"):
                devices = get_devices()
                if devices:
                    if len(devices) > 1:
                        device_names = [device.hostname for device in devices]
                        device_param = SingleChoiceParameter("device",
                                                             device_names)
                        device = device_param.prompt("Device to use: ")
                    else:
                        device = devices[0].hostname
                    self.run(["lava-dispatch", "--target", device,
                              self.args.FILE])
            else:
                raise CommandError("Cannot find lava-dispatcher installation.")
        else:
            raise CommandError("The file '{0}' does not exists, or it is not "
                               "a file.".format(self.args.FILE))


class status(BaseCommand):

    """Retrieves the status of a job."""

    @classmethod
    def register_arguments(cls, parser):
        super(status, cls).register_arguments(parser)
        parser.add_argument("JOB_ID",
                            help=("Prints status information about the "
                                  "provided job id."),
                            nargs="?",
                            default="-1")

    def invoke(self):
        job_id = str(self.args.JOB_ID)
        if job_id == "-1":
            # Get the value from the config and ask the user which one to look.
            job_ids_parameter = ListParameter(JOBS_ID)
            job_ids_parameter.asked = True

            job_ids = self.config.get_from_backend(job_ids_parameter)
            if job_ids:
                job_ids = Parameter.deserialize(job_ids)
                job_id = SingleChoiceParameter("job_id",
                                               job_ids).prompt("Job ids: ")
            else:
                raise CommandError("No job ids stored. Please provide one "
                                   "on the command line.")

        server = self.authenticated_server()

        try:
            job_status = server.scheduler.job_status(job_id)

            status = job_status["job_status"].lower()
            bundle = job_status["bundle_sha1"]

            print >> sys.stdout, "\nJob id: {0}".format(job_id)
            print >> sys.stdout, ("Status: {0}".format(status))
            print >> sys.stdout, ("Bundle: {0}".format(bundle))

            # If a job has finished running, remove it from the list of
            # job ids.
            if job_ids and status != "running":
                job_ids.remove(job_id)
                job_ids_parameter.set(job_ids)
                self.config.put_parameter(job_ids_parameter)

        except xmlrpclib.Fault, exc:
            raise CommandError(str(exc))
