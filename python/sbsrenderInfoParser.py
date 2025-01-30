from subprocess import run, CompletedProcess
from pathlib import Path
from enum import Enum

from pysbs.context import Context
from pysbs.sbsenum import InputValueTypeEnum


def PrintDictRecur(d: dict, indent=0):
    for k, v in d.items():
        if type(v) is dict:
            PrintDictRecur(v, indent + 1)
        else:
            print(f"{' ' * indent}{k}:{v}")


def GetSBSARInfo(sbsarPath: str):
    installPath = Path(Context.getAutomationToolkitInstallPath())
    sbsrender_exe = installPath.joinpath("sbsrender.exe")
    sbsar = sbsarPath

    result: CompletedProcess = run([sbsrender_exe, "info", sbsar], capture_output=True)
    infoByte = result.stdout.decode()
    infos = tuple(map(lambda x: x.strip().split(' '), infoByte.strip().split('\r\n')))

    sbsarInfo = dict()
    currentGraph = None
    for l in infos:
        if l[0] == "GRAPH-URL":
            _, graph = l[1].split('//')
            d = {"INPUT": dict(), "OUTPUT": dict()}
            currentGraph = d
            sbsarInfo[graph] = d
            continue
        else:

            if l[0] == "INPUT":
                io, name, t = l
                currentGraph[io][name] = t
            elif l[0] == "OUTPUT":
                lenL = len(l)
                if lenL <= 1:
                    continue
                elif lenL == 3:
                    io, name, t = l
                    currentGraph[io][name] = t
                    continue
                elif lenL == 2:
                    io, name = l
                    currentGraph[io][name] = "NO_USAGE"
                    continue
                else:
                    io, name, *usage = l
                    currentGraph[io][name] = "MULTIPLE_USAGE"
                    continue
            elif l[0] == "PRESET":
                io, name = l
                if io not in currentGraph:
                    currentGraph[io] = list()
                currentGraph[io].append(name)
            else:
                print(l[0])
    return sbsarInfo
