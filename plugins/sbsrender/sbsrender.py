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


def Quote(s: str):
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
        self.StdoutHandling = True

        # PopupHandling should be enabled if required in your plugin
        self.PopupHandling = False

        # Set the stdout handlers.
        # self.AddStdoutHandlerCallback("WARNING:.*").HandleCallback += self.HandleStdoutWarning
        # self.AddStdoutHandlerCallback("ERROR:(.*)").HandleCallback += self.HandleStdoutError

        # Set the popup ignorers.
        # self.AddPopupIgnorer("Popup 1")
        # self.AddPopupIgnorer("Popup 2")

        # Set the popup handlers.
        # self.AddPopupHandler("Popup 3", "OK")
        # self.AddPopupHandler("Popup 4", "Do not ask me this again;Continue")

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

    def HandleStdoutWarning(self):
        """Callback for when a line of stdout contains a WARNING message."""
        self.LogWarning(self.GetRegexMatch(0))

    def HandleStdoutError(self):
        """Callback for when a line of stdout contains an ERROR message."""
        self.FailRender("Detected an error: " + self.GetRegexMatch(1))

    def RenderArg(self):
        sbsrender = self.HandleRenderExecutable()

        sbsarFile = self.GetPluginInfoEntry("input").replace('\\', '/')
        sbsarFileQ = Quote(sbsarFile)

        csvFile = self.GetPluginInfoEntry("csvFile")
        csvFileQ = Quote(csvFile)

        if not os.path.exists(sbsarFile):
            self.FailRender(f"SBSAR file not exist: {sbsarFile}")
            return ""

        if not os.path.exists(csvFile):
            self.FailRender(f"CSV file not exists: {csvFile}")
            return f""

        outputsize = ','.join(map(lambda x: str(int(log2(int(x)))), self.GetPluginInfoEntry("outputsize").split(',')))
        parms = [
            "render",
            "--input", f"\"{sbsarFile}\"",
            "--input-graph", self.GetPluginInfoEntry("input-graph"),
            "--output-bit-depth", self.GetPluginInfoEntry("output-bit-depth"),
            "--output-format", self.GetPluginInfoEntry("output-format"),
            "--output-name", self.GetPluginInfoEntry("output-name"),
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
            seed = self.GetPluginInfoEntry("randomseed")

        rSeed = f"$randomseed@{seed}"
        print(rSeed)
        parms.append(rSeed)

        # print(parms)

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

                    for h, v in zip(header, row):
                        if v != "":
                            parms.append(f"--set-value")
                            parms.append(f"{h}@{v.replace('|', ',')}")
                            print(f"{h} @ {v.replace('|', ',')}")
                    break
        return ' '.join(parms)
