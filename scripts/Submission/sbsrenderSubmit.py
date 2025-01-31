import os.path
from csv import excel
from math import expm1

from Deadline.Scripting import RepositoryUtils
from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

from functools import partial

from Deadline.Scripting import RepositoryUtils

from SubmitDLJob import SubmitJob
from sbsrenderInfoParser import GetSBSARInfo, SBSARInfo, GraphInfo

submitter = partial(SubmitJob, "sbsrender")

try:
    from typing import Any
except ImportError:
    pass

# Globals =================================
g_dialog = DeadlineScriptDialog()
g_input = None
g_inputGraph = None
g_sbsarDict = None
g_output = None
g_usageOn = None
g_outBitDepth = None
g_outName = None
g_presets = None
g_randomSeed = None
g_diffEachSeed = None

# params
## job


## plugin inputs

### deadline
PARM_CSV = "parmCSVFile"
### sbsrender
INPUT = "input"
INPUT_GRAPH = "input-graph"
OUT_DEPTH = "output-bit-depth"

OUTPUT = "output"
OUTPUT_PATH = "output-path"
OUTPUT_NAME = "output-name"
OUTPUT_FORMAT = "output-format"
PRESET = "use-preset"


# todo : preset 추가
# =========================================
def exceptAll(func):
    def wrapper(*args):
        try:
            func(*args)
        except Exception as e:
            print(e)

    return wrapper


def __main__(*args):
    global g_input, g_dialog, g_inputGraph, g_usageOn, g_output, g_outBitDepth, g_outName, g_presets, g_randomSeed, g_diffEachSeed
    # Tab Start

    g_dialog.AddTabControl("Deadline Job Controls", 0, 0)

    # Tab Page(SBS Render Options) Start
    g_dialog.AddTabPage("SBS Render Options")
    g_dialog.AddGrid()
    g_dialog.AddControlToGrid("IOSep", "SeparatorControl", "I/O options", r := 0, c := 0, colSpan=5)

    g_dialog.AddControlToGrid(f"{INPUT}Label", "LabelControl", "SBSAR File", r := r + 1, c := 0, expand=False)
    g_input = g_dialog.AddSelectionControlToGrid(INPUT, "FileBrowserControl", "",
                                                 "Substance Archaive File (*.sbsar)",
                                                 r, c := c + 1, colSpan=2)

    g_dialog.AddControlToGrid(f"{INPUT_GRAPH}Label", "LabelControl", "Input Graph", r := r, c := c + 2)
    g_inputGraph = g_dialog.AddComboControlToGrid(INPUT_GRAPH, "ComboControl", "", ("",), r, c := c + 1,
                                                  expand=True)
    g_inputGraph.currentTextChanged.connect(OnGraphChanged)

    g_dialog.AddControlToGrid(f"{OUTPUT}Label", "LabelControl", "Outputs to export", r := r + 1, c := 0)
    g_output = g_dialog.AddControlToGrid(OUTPUT, "TextControl", "", r, c := c + 1, colSpan=3)
    g_usageOn = g_dialog.AddSelectionControlToGrid("outputBasedUsage", "CheckBoxControl", False,
                                                   "Output Based Usage",
                                                   r := r, c := c + 3)
    g_usageOn.toggled.connect(UsageToggled)

    g_dialog.AddControlToGrid(f"{PARM_CSV}Label", "LabelControl", "Parm CSV File", r := r + 1, c := 0, expand=False)
    g_dialog.AddSelectionControlToGrid(PARM_CSV, "FileBrowserControl", "", "Comma Seperated Value (*.csv)", r,
                                       c := c + 1, colSpan=2)
    g_dialog.AddControlToGrid(f"{PRESET}Label", "LabelControl", "Preset", r, c := c + 2)
    g_presets = g_dialog.AddComboControlToGrid(PRESET, "ComboControl", "", ("",), r, c := c + 1)

    g_dialog.AddControlToGrid(f"{OUT_DEPTH}Label", "LabelControl", "Output Bit Depth", r := r + 1, c := 0,
                              expand=False)
    g_outBitDepth = g_dialog.AddComboControlToGrid(OUT_DEPTH, "ComboControl", "16", ("8", "16", "16f", "32f"), r,
                                                   c := c + 1)

    g_dialog.AddControlToGrid(f"{OUTPUT_PATH}Label", "LabelControl", "Destination Path", r := r + 1, c := 0,
                              expand=False)
    g_dialog.AddSelectionControlToGrid(OUTPUT_PATH, "FolderBrowserControl", "", "", r, c := c + 1, colSpan=4)

    g_dialog.AddControlToGrid(f"{OUTPUT_NAME}Label", "LabelControl", "File Name Pattern", r := r + 1, c := 0,
                              expand=False)
    g_outName = g_dialog.AddControlToGrid(OUTPUT_NAME, "TextControl", "{inputGraphUrl}_{outputNodeName}", r,
                                          c := c + 1,
                                          colSpan=3, expand=True)
    g_dialog.AddComboControlToGrid(OUTPUT_FORMAT, "ComboControl", "png",
                                   ("surface", "dds", "bmp", "jpg", "jif", "jpeg", "jpe", "png", "tga", "targa",
                                    "tif",
                                    "tiff", "wap", "wbmp", "wbm", "psd", "psb", "hdr", "exr", "webp"), r,
                                   c := 4)

    g_dialog.AddControlToGrid("outputsizeLabel", "LabelControl", "Output Size(x, y)", r := r + 1, c := 0,
                              expand=False)
    sizeTuple = tuple([str(2 ** i) for i in range(0, 14)])

    g_dialog.AddComboControlToGrid("outputsizeX", "ComboControl", "1024", sizeTuple, r, c := c + 1, colSpan=2)
    g_dialog.AddComboControlToGrid("outputsizeY", "ComboControl", "1024", sizeTuple, r, c := c + 2, colSpan=2)

    g_dialog.AddControlToGrid("randomseedLabel", "LabelControl", "Random seed", r := r + 1, c := 0, expand=False)
    g_randomSeed = g_dialog.AddRangeControlToGrid("randomseed", "SliderControl", 0, 0, 2147483647 / (2 ** 7), 0, 1,
                                                  r,
                                                  c := c + 1, colSpan=2)
    g_diffEachSeed = g_dialog.AddSelectionControlToGrid("diffEachSeed", "CheckBoxControl", False,
                                                        "Randomize seed each time",
                                                        r := r, c := c + 2, colSpan=2)
    g_diffEachSeed.toggled.connect(lambda x: g_randomSeed.setEnabled(not x))

    g_dialog.EndGrid()

    g_dialog.EndTabPage()
    # Tab Page(SBS Render Options) End

    # Tab Page(Job Options) End
    g_dialog.AddTabPage("Job Options")
    g_dialog.EndTabPage()
    # Tab Page(Job Options) End

    g_dialog.EndTabControl()
    # Tab End

    # Grid: Buttons
    g_dialog.AddGrid()
    g_dialog.AddControlToGrid("Separator2", "SeparatorControl", "Execution", r := 0, c := 0, colSpan=3)
    submitButton = g_dialog.AddControlToGrid("submitButton", "ButtonControl", "Submit", r := r + 1, c := 0)
    testButton = g_dialog.AddControlToGrid("testButton", "ButtonControl", "TEST", r, c := c + 1)

    g_input.ValueModified.connect(OnSBSARInputChanged)

    submitButton.ValueModified.connect(Submit)
    testButton.ValueModified.connect(Test)
    g_dialog.EndGrid()
    # End grid: Buttons

    g_dialog.ShowDialog()


def UsageToggled(toggled):
    """
    Slot for the usage checkbox.
    Modify the output based on the usage.
    :param toggled:
    :return:
    """
    global g_output, g_sbsarDict
    try:
        currGraph = g_inputGraph.currentText()
        if currGraph == "":
            return

        g_output.clear()
        assert currGraph in g_sbsarDict, f"{currGraph} not in current SBSAR file."

        gDict = g_sbsarDict[currGraph]

        usageOn = toggled

        if usageOn:  # Usage based output
            txt = ' '.join(gDict.Usage)
            g_output.setText(txt)
            g_outName.setText("{inputGraphUrl}_{outputUsages}")

        else:  # Name based output
            txt = ' '.join(gDict.Output)
            g_output.setText(txt)
            g_outName.setText("{inputGraphUrl}_{outputNodeName}")



    except Exception as e:
        print(e)


def OnGraphChanged(newGraph=""):
    """
    Reset the output and preset based on the current graph.
    Internally call UsageToggled to modify output.
    """
    global g_sbsarDict, g_inputGraph, g_output, g_presets
    if newGraph == "":
        return

    usageOn = g_usageOn.isChecked()
    UsageToggled(usageOn)

    if g_sbsarDict.HasPreset:
        g_presets.clear()
        g_presets.addItem("No preset")
        for p in g_sbsarDict.Preset:
            g_presets.addItem(p)
        g_presets.setEnabled(True)
    else:
        g_presets.clear()
        g_presets.addItem("Not available")
        g_presets.setDisabled(True)


def OnSBSARInputChanged(args):
    global g_sbsarDict, g_inputGraph, g_output

    if os.path.exists(args.TheValue):
        sbsInfo = GetSBSARInfo(args.TheValue)
        g_sbsarDict = sbsInfo

    g_inputGraph.clear()
    for f in dir(g_inputGraph):
        print(f)
    return
    try:
        g_inputGraph.addItem("Select")
    except Exception as e:
        print(e)
        return

    return
    OnGraphChanged(g_sbsarDict.GraphNames[0])


def Test():
    global g_output
    print(type(g_output).__mro__)


def Submit(*args):
    global g_dialog

    sbsarFile = g_dialog.GetValue("input")
    csvFile = g_dialog.GetValue("parmCSVFile")

    job_info = dict()
    job_info["Name"] = "SBSAR Render"

    if os.path.exists(csvFile):
        with open(csvFile, "r") as f:
            job_info["Frames"] = f"1-{len(f.readlines()) - 1}"
    else:
        g_dialog.ShowMessageBox("No CSV File", "Error", ("OK",))

    if not os.path.exists(sbsarFile):
        g_dialog.ShowMessageBox("No SBSAR File", "Error", ("OK",))

    plugin_info = {"input": sbsarFile,
                   "csvFile": csvFile}

    result = submitter(job_info, plugin_info)
    g_dialog.ShowMessageBox(result, "Submission Result", ("OK",))
