#!/usr/bin/env python3
import os.path
from pathlib import Path
from csv import reader
from math import log2
from sys import maxsize
from random import randint
from subprocess import run

from Deadline.Plugins import *

import pysbs

from System.Diagnostics import *


# from Deadline.Scripting import StringUtils

def GetDeadlinePlugin():
    """This is the function that Deadline calls to get an instance of the
    main DeadlinePlugin class.
    """
    return SbsRenderPlugin()


def CleanupDeadlinePlugin(deadlinePlugin):
    """This is the function that Deadline calls when the plugin is no
    longer in use so that it can get cleaned up.
    """
    deadlinePlugin.Cleanup()


def DQuote(s: str):
    return f"\"{s}\""


def SQuote(s: str):
    return f"\'{s}\'"


class SbsRenderPlugin(DeadlinePlugin):
    """This is the main DeadlinePlugin class for MyPlugin."""

    def __init__(self):
        """Hook up the callbacks in the constructor."""
        super().__init__()  # Required in Deadline 10.3 and later.
        self.InitializeProcessCallback += self.InitializeProcess

    def Cleanup(self):
        """Clean up the plugin."""
        # Clean up stdout handler callbacks.
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback

        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback

    def InitializeProcess(self):
        """Called by Deadline to initialize the process."""
        # Set the plugin specific settings.
        self.SingleFramesOnly = True
        self.PluginType = PluginType.Simple

        # Set the ManagedProcess specific settings.
        self.ProcessPriority = ProcessPriorityClass.BelowNormal
        self.UseProcessTree = True

        # StdoutHandling should be enabled if required in your plugin
        self.StdoutHandling = False

        # PopupHandling should be enabled if required in your plugin
        self.PopupHandling = False

        self.RenderExecutableCallback += self.HandleRenderExecutable
        self.RenderArgumentCallback += self.RenderArg

    def HandleRenderExecutable(self):
        installPath = Path(pysbs.context.Context.getAutomationToolkitInstallPath())
        sbsrender_exe = installPath.joinpath("sbsrender.exe")
        if not sbsrender_exe.exists():
            self.FailRender(f"sbsrender.exe not found at: {sbsrender_exe}")
            return
        print(f"Found sbsrender.exe at: {sbsrender_exe}")

        return str(sbsrender_exe)

    def RenderArg(self):
        sbsrender = self.HandleRenderExecutable()

        sbsarFile = self.GetPluginInfoEntry("input").replace('\\', '/')
        sbsarFileQ = SQuote(sbsarFile)

        csvFile = self.GetPluginInfoEntry("csvFile")
        csvFileQ = SQuote(csvFile)

        if not os.path.exists(sbsarFile):
            self.FailRender(f"SBSAR file not exist: {sbsarFile}")
            return ""

        if not os.path.exists(csvFile):
            self.FailRender(f"CSV file not exists: {csvFile}")
            return f""

        outputsize = ','.join(map(lambda x: str(int(log2(int(x)))),
                                  self.GetPluginInfoEntryWithDefault("outputsize", "1024,1024").split(',')))
        parms = [
            "render",
            "--input", f"\"{sbsarFile}\"",
            "--input-graph", self.GetPluginInfoEntry("input-graph"),
            "--output-bit-depth", self.GetPluginInfoEntryWithDefault("output-bit-depth", "8"),
            "--output-format", self.GetPluginInfoEntryWithDefault("output-format", "png"),
            "--output-name", self.GetPluginInfoEntryWithDefault("output-name", "{inputName}_{inputGraphUrl}_{outputNodeName}"),
            "--set-value", f"$outputsize@{outputsize}",
        ]

        outputBasedUsage = self.GetPluginInfoEntry("outputBasedUsage") == "True"
        output = self.GetPluginInfoEntry("output").split(' ')
        if outputBasedUsage:
            for o in output:
                parms.append(f"--input-graph-output-usage")
                parms.append(o)
        else:
            for o in output:
                parms.append(f"--input-graph-output")
                parms.append(o)

        parms.append("--set-value")
        diffEachSeed = self.GetPluginInfoEntryWithDefault("diffEachSeed", "False") == "True"
        seed = 0
        if diffEachSeed:
            seed = randint(0, int(2147483647 / (2 ** 7)))

        else:
            seed = self.GetPluginInfoEntryWithDefault("randomseed", "0")

        rSeed = f"$randomseed@{seed}"
        self.LogInfo(f"Random Seed: {seed}")
        parms.append(rSeed)

        outputPath = Path(self.GetPluginInfoEntry("output-path"))

        with open(csvFile, "r") as f:
            csvReader = reader(f)
            startFrame = self.GetStartFrame()
            header = next(csvReader)
            dType = next(csvReader)
            for i, row in enumerate(csvReader):
                if i == startFrame:
                    d = outputPath.joinpath(f"{i:04}")
                    d.mkdir(exist_ok=True)
                    parms.append('--output-path')
                    parms.append(f"\"{d}\"".replace('\\', '/'))

                    failed = []
                    parsers = {
                        "INTEGER": int,
                        "FLOAT": float,
                    }

                    for h, v, d in zip(header, row, dType):
                        if v != "":
                            if d.startswith("INTEGER") or d.startswith("FLOAT"):
                                parser = parsers[d[:-1]]

                                parsed = tuple(map(lambda x: str(parser(x)), v.split('|')))
                                required = int(d[-1])
                                put = len(parsed)
                                if required != put:
                                    failed.append(f"{h} required {required} value(s), but got {put} value(s).")
                                    continue

                                parms.append(f"--set-value")
                                value = ','.join(parsed)
                                parms.append(f"{h}@{value}")

                            # elif d.startswith("FLOAT"):
                            #     parsed = tuple(map(lambda x: str(float(x)), v.split('|')))
                            #     required = int(d[-1])
                            #     put = len(parsed)
                            #     if required != put:
                            #         failed.append(f"Required {required} values, but got {put} values for {h}")
                            #         continue
                            #     parms.append(f"--set-value")
                            #     value = ','.join(parsed)
                            #     parms.append(f"{h}@{value}")
                            #
                            #     print(f"{h}@{value}")

                            elif d.startswith("IMAGE"):
                                if not os.path.exists(v):
                                    failed.append(f"Image not found: {v}")
                                    continue
                                parms.append(f"--set-entry")
                                parms.append(f"{h}@\"{v}\"")

                    if failed:
                        for i in failed:
                            self.LogWarning(f"Image not found: {i}")
                        self.FailRender(f"More than input parsing failed.")
                        return ""
                    break
        return ' '.join(parms)
