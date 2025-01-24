#!/usr/bin/env python3
import os.path

from Deadline.Plugins import *
from pathlib import Path
from csv import reader

import pysbs

from System.Diagnostics import *


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
        self.SingleFramesOnly = False
        self.PluginType = PluginType.Simple

        # Set the ManagedProcess specific settings.
        self.ProcessPriority = ProcessPriorityClass.BelowNormal
        self.UseProcessTree = True

        # StdoutHandling should be enabled if required in your plugin
        self.StdoutHandling = True

        # PopupHandling should be enabled if required in your plugin
        self.PopupHandling = True

        # Set the stdout handlers.
        self.AddStdoutHandlerCallback(
            "WARNING:.*").HandleCallback += self.HandleStdoutWarning
        self.AddStdoutHandlerCallback(
            "ERROR:(.*)").HandleCallback += self.HandleStdoutError

        # Set the popup ignorers.
        self.AddPopupIgnorer("Popup 1")
        self.AddPopupIgnorer("Popup 2")

        # Set the popup handlers.
        self.AddPopupHandler("Popup 3", "OK")
        self.AddPopupHandler("Popup 4", "Do not ask me this again;Continue")

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
        sbsarFile = self.GetPluginInfoEntry("sbsarFile")
        csvFile = self.GetPluginInfoEntry("csvFile")
        startFrame = self.GetStartFrame()
        if os.path.exists(csvFile):
            with open(csvFile, "r") as f:
                csvReader = reader(f)
                for i, row in enumerate(csvReader):
                    if i == startFrame:
                        print(row)
                        return f"--verbose info {sbsarFile}"  # f"{sbsarFile} {csvFile}"
        return f"--verbose info {sbsarFile}"

    def HandleStdoutWarning(self):
        """Callback for when a line of stdout contains a WARNING message."""
        self.LogWarning(self.GetRegexMatch(0))

    def HandleStdoutError(self):
        """Callback for when a line of stdout contains an ERROR message."""
        self.FailRender("Detected an error: " + self.GetRegexMatch(1))
