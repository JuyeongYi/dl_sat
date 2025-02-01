import os.path
from functools import partial
from pathlib import Path

# from Deadline.Scripting import RepositoryUtils
from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog
from SubmitDLJob import SubmitJob
from sbsrenderInfoParser import GetSBSARInfo

submitter = partial(SubmitJob, "sbsrender")

try:
    from typing import Any
except ImportError:
    pass

DEBUG = True

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
g_outputPath = None
g_parmCSV = None

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


# =========================================
def exceptAll(func):
    def wrapper(*args):
        try:
            func(*args)
        except Exception as e:
            print(e)

    return wrapper


def __main__(*args):
    global g_input, g_dialog, g_inputGraph, g_usageOn, g_output, g_outBitDepth, g_outName, g_presets, g_randomSeed
    global g_diffEachSeed, g_outputPath, g_parmCSV
    # Tab Start
    g_dialog.AddTabControl("Deadline Job Controls", 0, 0)

    # Tab Page(SBS Render Options) Start
    g_dialog.AddTabPage("SBS Render Options")
    g_dialog.AddGrid()
    g_dialog.AddControlToGrid("IOSep", "SeparatorControl", "I/O options", r := 0, c := 0, colSpan=5)

    # R1 : SBSAR File, Input Graph
    g_dialog.AddControlToGrid(f"{INPUT}Label", "LabelControl", "SBSAR File", r := r + 1, c := 0, expand=False)
    g_input = g_dialog.AddSelectionControlToGrid(INPUT, "FileBrowserControl", "", "Substance Archaive File (*.sbsar)",
                                                 r, c := c + 1, colSpan=2)
    g_dialog.AddControlToGrid(f"{INPUT_GRAPH}Label", "LabelControl", "Input Graph", r := r, c := c + 2)
    g_inputGraph = g_dialog.AddComboControlToGrid(INPUT_GRAPH, "ComboControl", "", ("",), r, c := c + 1, expand=True)
    g_inputGraph.currentTextChanged.connect(OnGraphChanged)

    # R2 : Destination Path
    g_dialog.AddControlToGrid(f"{OUTPUT_PATH}Label", "LabelControl", "Destination Path", r := r + 1, c := 0,
                              expand=False)
    g_outputPath = g_dialog.AddSelectionControlToGrid(OUTPUT_PATH, "FolderBrowserControl", "", "", r, c := c + 1,
                                                      colSpan=4)

    # R3 : Parm CSV
    g_dialog.AddControlToGrid(f"{PARM_CSV}Label", "LabelControl", "Parm CSV File", r := r + 1, c := 0, expand=False)
    g_parmCSV = g_dialog.AddSelectionControlToGrid(PARM_CSV, "FileBrowserControl", "", "Comma Seperated Value (*.csv)",
                                                   r, c := c + 1, colSpan=4)

    # R4 : Make Parm CSV
    mkParmCSVBtn = g_dialog.AddControlToGrid("makeParmCSV", "ButtonControl",
                                             "Make parm CSV for chosen file and graph to destination",
                                             r := r + 1, c := 1, colSpan=4)
    mkParmCSVBtn.clicked.connect(MakeParmCSV)

    # R5: Output, Output Based Usage
    g_dialog.AddControlToGrid(f"{OUTPUT}Label", "LabelControl", "Outputs to export", r := r + 1, c := 0)
    g_output = g_dialog.AddControlToGrid(OUTPUT, "TextControl", "", r, c := c + 1, colSpan=3)
    g_usageOn = g_dialog.AddSelectionControlToGrid("outputBasedUsage", "CheckBoxControl", False, "Output Based Usage",
                                                   r := r, c := c + 3)
    g_usageOn.toggled.connect(UsageToggled)

    # R6 : Preset, Output Bit Depth
    g_dialog.AddControlToGrid(f"{PRESET}Label", "LabelControl", "Preset", r := r + 1, c := 0)
    g_presets = g_dialog.AddComboControlToGrid(PRESET, "ComboControl", "", ("",), r, c := c + 1, colSpan=2)

    g_dialog.AddControlToGrid(f"{OUT_DEPTH}Label", "LabelControl", "Output Bit Depth", r := r, c := c + 2, expand=False)
    g_outBitDepth = g_dialog.AddComboControlToGrid(OUT_DEPTH, "ComboControl", "16", ("8", "16", "16f", "32f"), r,
                                                   c := c + 1)

    # R7 : Output Name, Output Format
    g_dialog.AddControlToGrid(f"{OUTPUT_NAME}Label", "LabelControl", "File Name Pattern", r := r + 1, c := 0,
                              expand=False)
    g_outName = g_dialog.AddControlToGrid(OUTPUT_NAME, "TextControl", "{inputGraphUrl}_{outputNodeName}", r, c := c + 1,
                                          colSpan=3, expand=True)
    g_dialog.AddComboControlToGrid(OUTPUT_FORMAT, "ComboControl", "png",
                                   ("surface", "dds", "bmp", "jpg", "jif", "jpeg", "jpe", "png", "tga", "targa",
                                    "tif", "tiff", "wap", "wbmp", "wbm", "psd", "psb", "hdr", "exr", "webp"), r, c := 4)

    # R8 : Output Size
    g_dialog.AddControlToGrid("outputsizeLabel", "LabelControl", "Output Size(x, y)", r := r + 1, c := 0,
                              expand=False)
    sizeTuple = tuple([str(2 ** i) for i in range(0, 14)])

    g_dialog.AddComboControlToGrid("outputsizeX", "ComboControl", "1024", sizeTuple, r, c := c + 1, colSpan=2)
    g_dialog.AddComboControlToGrid("outputsizeY", "ComboControl", "1024", sizeTuple, r, c := c + 2, colSpan=2)

    # R9 : Random Seed
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
    if DEBUG:
        g_dialog.AddTabPage("Debug Mode")
        g_dialog.AddGrid()
        printSBSAR = g_dialog.AddControlToGrid("printSBSAR", "ButtonControl", "printSBSAR", r := 0, c := 0)
        printSBSAR.clicked.connect(lambda x: print(g_sbsarDict))

        printGraph = g_dialog.AddControlToGrid("printGRAPH", "ButtonControl", "printSBSAR", r, c := c + 1)
        printGraph.clicked.connect(lambda x: print(g_sbsarDict[g_inputGraph.currentText()]))
        g_dialog.EndGrid()
        g_dialog.EndTabPage()

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

    g_dialog.ShowDialog(False)


def UsageToggled(toggled):
    """
    Slot for the usage checkbox.
    Modify the output based on the usage.
    :param toggled:
    :return:
    """
    global g_output, g_sbsarDict

    currGraph = g_inputGraph.currentText()
    if currGraph == "":
        return

    g_output.clear()

    currGraph = g_sbsarDict[currGraph]
    usageOn = toggled

    if usageOn:  # Usage based output
        txt = ' '.join(currGraph.Usage)
        g_output.setText(txt)
        try:
            if currGraph.UsageOverraped:
                g_outName.setText("{inputGraphUrl}_{outputNodeName}_{outputUsages}")
            else:
                g_outName.setText("{inputGraphUrl}_{outputUsages}")
        except Exception as e:
            print(e)

    else:  # Name based output
        txt = ' '.join([x[0] for x in currGraph.Output])
        g_output.setText(txt)
        g_outName.setText("{inputGraphUrl}_{outputNodeName}")


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

    currGraph = g_sbsarDict[newGraph]
    g_presets.clear()
    try:
        if currGraph.HasPreset:
            g_presets.addItem("No preset")
            g_presets.addItems(currGraph.Preset)
            g_presets.setEnabled(True)
        else:
            g_presets.addItem("Not available")
            g_presets.setDisabled(True)
    except Exception as e:
        print(e)


def OnSBSARInputChanged(args):
    global g_sbsarDict, g_inputGraph, g_output

    if os.path.exists(args.TheValue):
        g_sbsarDict = GetSBSARInfo(args.TheValue)

    g_inputGraph.clear()
    g_inputGraph.addItems(g_sbsarDict.GraphNames)

    # OnGraphChanged(g_sbsarDict.GraphNames[0])


def MakeParmCSV():
    global g_sbsarDict, g_inputGraph, g_outputPath, g_dialog, g_parmCSV
    sbsarPath = g_sbsarDict.Path
    graph = g_inputGraph.currentText()
    outStr = g_outputPath.TheValue
    outPath = Path(g_outputPath.TheValue) if outStr != "" else ""

    if not sbsarPath.is_file():
        g_dialog.ShowMessageBox(f"{sbsarPath} not exists.", "SBSAR Error")
        return

    if outPath == "" or not outPath.is_dir():
        g_dialog.ShowMessageBox(f"{outPath} is neither exist nor a directory", "Output Path Error")
        return

    csvPath = outPath.joinpath(f"{sbsarPath.stem}_{graph}.csv")
    try:
        graph = g_sbsarDict[graph]
        parmName = ','.join([x[0] for x in graph.Input if not x[0].startswith("$")])
        parmType = ','.join([x[1] for x in graph.Input if not x[0].startswith("$")])

        with open(csvPath, "w") as fp:
            fp.write(f"{parmName}\n{parmType}\n")
            sampleLow = ',' * (len(parmName) - 1)
            fp.write(f"{sampleLow}\n")

        g_parmCSV.TheValue = str(csvPath)
    except Exception as e:
        g_dialog.ShowMessageBox(f"Error: {e}", "Error")


def Test():
    global g_output
    print(type(g_output).__mro__)


def Submit(*args):
    global g_dialog

    job_info = dict()

    csvFile = g_dialog.GetValue(PARM_CSV)
    if os.path.exists(csvFile):
        with open(csvFile, "r") as f:
            lines = f.readlines()
            lineLines = len(lines)
            if lineLines < 2:
                g_dialog.ShowMessageBox("CSV File is empty or only headers.", "Error", ("OK",))
                return
            elif lineLines == 3:
                job_info["Frames"] = f"0"
            else:
                job_info["Frames"] = f"0-{lineLines - 3}"
    else:
        g_dialog.ShowMessageBox("No CSV File", "Error", ("OK",))
        return

    sbsarFile = g_dialog.GetValue(INPUT)
    if not os.path.exists(sbsarFile):
        g_dialog.ShowMessageBox("No SBSAR File", "Error", ("OK",))
        return

    sbsarFilePath = Path(sbsarFile)
    csvFilePath = Path(csvFile)
    inputGraph = g_dialog.GetValue(INPUT_GRAPH)

    job_info["Name"] = f"{sbsarFilePath.stem}({inputGraph}) w/ {csvFilePath.stem}"

    plugin_info = {"input": sbsarFile,
                   "csvFile": csvFile,
                   INPUT_GRAPH: g_dialog.GetValue(INPUT_GRAPH),
                   OUT_DEPTH: g_dialog.GetValue(OUT_DEPTH),
                   OUTPUT: g_dialog.GetValue(OUTPUT),
                   OUTPUT_PATH: g_dialog.GetValue(OUTPUT_PATH),
                   OUTPUT_NAME: g_dialog.GetValue(OUTPUT_NAME),
                   OUTPUT_FORMAT: g_dialog.GetValue(OUTPUT_FORMAT),
                   "outputBasedUsage": g_dialog.GetValue("outputBasedUsage"),
                   }

    if g_presets.isEnabled():
        preset = g_dialog.GetValue(PRESET)
        if preset != "No preset":
            plugin_info[PRESET] = preset

    diffEachSeed = g_dialog.GetValue("diffEachSeed")

    if diffEachSeed:
        plugin_info["diffEachSeed"] = True
    else:
        plugin_info["randomseed"] = g_dialog.GetValue("randomseed")

    outputsizeX = g_dialog.GetValue("outputsizeX")
    outputsizeY = g_dialog.GetValue("outputsizeY")
    plugin_info["outputsize"] = f"{outputsizeX},{outputsizeY}"

    result = submitter(job_info, plugin_info)
    g_dialog.ShowMessageBox(result, "Submission Result", ("OK",))
