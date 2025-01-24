# Copyright Epic Games, Inc. All Rights Reserved
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

from Deadline.Scripting import ClientUtils
from pathlib import Path

import pysbs
import re

jobIdFinder = re.compile("[0-9a-fA-F]{24}")


def Test():
    print("Hello World")


def SubmitJob(name, job_info, plugin_info, aux_files=None):
    """
    Creates a job and plugin file and submits it to deadline as a job
    :param name: Name of the plugin
    :param job_info: The job dictionary
    :type job_info dict
    :param plugin_info: The plugin dictionary
    :type plugin_info dict
    :param aux_files: The files submitted to the farm
    :type aux_files list
    """

    # Create a job file
    job_info["Plugin"] = name

    dlTempPath = Path(ClientUtils.GetDeadlineTempPath())
    JobInfoFilename = dlTempPath.joinpath(f"{name}_job_info.job")

    # Get a job info file writer
    # writer = StreamWriter(JobInfoFilename, False, Encoding.Unicode)

    with open(JobInfoFilename, "w") as writer:
        for key, value in job_info.items():
            writer.write(f"{key}={value}\n")

    # Create a plugin file
    PluginInfoFileName = dlTempPath.joinpath(f"{name}_plugin_info.job")

    # Get a plugin info file writer
    with open(PluginInfoFileName, "w") as writer:
        for key, value in plugin_info.items():
            writer.write(f"{key}={value}\n")

        # Add Aux Files if any
        if aux_files:
            for index, aux_files in enumerate(aux_files):
                writer.write(f"File{index}={aux_files}\n")

    # Create the commandline arguments
    args = [JobInfoFilename, PluginInfoFileName]

    # Add aux files to the plugin data
    if aux_files:
        for scene_file in aux_files:
            args.append(scene_file)

    results = ClientUtils.ExecuteCommandAndGetOutput(args)
    print(results)

    found = jobIdFinder.findall(results)
    if found:
        return found[0]
    else:
        return None
