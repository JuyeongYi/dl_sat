import os.path

from Deadline.Scripting import RepositoryUtils
from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

from functools import partial

from SubmitDLJob import SubmitJob

submitter = partial(SubmitJob, "sbsrender")

try:
    from typing import Any
except ImportError:
    pass

scriptDialog = DeadlineScriptDialog()


def __main__(*args):
    global scriptDialog
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid("Separator1", "SeparatorControl", "Job Description", 0, 0, colSpan=3)
    scriptDialog.AddControlToGrid("sbsarFileLabel", "LabelControl", "SBSAR File", 1, 0, expand=False)
    scriptDialog.AddSelectionControlToGrid("sbsarFile", "FileBrowserControl", "", "Substance Archaive Files (*.sbsar)",
                                           1, 1, colSpan=2)
    scriptDialog.AddControlToGrid("parmCSVLabel", "LabelControl", "Parm CSV File", 2, 0, expand=False)
    scriptDialog.AddSelectionControlToGrid("parmCSVFile", "FileBrowserControl", "", "Comma Seperated Value (*.csv)",
                                           2, 1, colSpan=2)
    scriptDialog.AddControlToGrid("dstPathLabel", "LabelControl", "Destination Path", 3, 0, expand=False)
    scriptDialog.AddSelectionControlToGrid("dstPath", "FolderBrowserControl", "", "", 3, 1, colSpan=2)
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid("Separator2", "SeparatorControl", "Execution", 0, 0, colSpan=3)
    submitButton = scriptDialog.AddControlToGrid("Separator2", "ButtonControl", "Submit", 1, 1)
    submitButton.ValueModified.connect(Submit)

    scriptDialog.EndGrid()

    scriptDialog.show()


def Submit(*args):
    global scriptDialog

    sbsarFile = scriptDialog.GetValue("sbsarFile")
    csvFile = scriptDialog.GetValue("parmCSVFile")

    job_info = dict()
    job_info["Name"] = "SBSAR Render"

    if os.path.exists(csvFile):
        with open(csvFile, "r") as f:
            job_info["Frames"] = f"1-{len(f.readlines()) - 1}"
    else:
        scriptDialog.ShowMessageBox("No CSV File", "Error", ("OK",))

    if not os.path.exists(sbsarFile):
        scriptDialog.ShowMessageBox("No SBSAR File", "Error", ("OK",))

    plugin_info = {"sbsarFile": sbsarFile,
                   "csvFile": csvFile}

    result = submitter(job_info, plugin_info)
    scriptDialog.ShowMessageBox(result, "Submission Result", ("OK",))
