from subprocess import run, CompletedProcess, CREATE_NO_WINDOW
from pathlib import Path
from enum import Enum
from queue import Queue

from pysbs.context import Context
from pysbs.sbsenum import InputValueTypeEnum


def PrintDictRecur(d: dict, indent=0):
    for k, v in d.items():
        if type(v) is dict:
            PrintDictRecur(v, indent + 1)
        else:
            print(f"{' ' * indent}{k}:{v}")


class GraphInfo:
    __name: str

    def __init__(self, graphInfo: str):
        lines = list(map(lambda x: x.strip(), graphInfo.split('\r\n')))
        self.__name = str(lines.pop(0).split('//')[-1].strip())
        inputs = []
        outputs = []
        presets = []
        graphusages = set()
        self.__usageOverraped = False

        for l in lines:
            toks = l.split(' ')
            if toks[0] == 'INPUT':
                inputs.append((toks[1], toks[2]))
            elif toks[0] == 'OUTPUT':
                lenTok = len(toks)
                if lenTok == 2:
                    outputs.append(toks[1])
                elif lenTok == 3:
                    usages = toks[2].split(',')
                    for u in usages:
                        self.__usageOverraped |= u in graphusages
                        graphusages.add(u)
                    outputs.append((toks[1], usages))
            elif toks[0] == 'PRESET':
                presets.append(toks[1])

        self.__inputs = tuple(inputs)
        self.__outputs = tuple(outputs)
        self.__presets = tuple(presets)
        self.__usages = tuple(graphusages)

    @property
    def Name(self):
        return self.__name

    @property
    def Input(self):
        return self.__inputs

    @property
    def Output(self):
        return self.__outputs

    @property
    def Preset(self):
        return self.__presets

    @property
    def HasPreset(self):
        return len(self.__presets) > 0

    @property
    def Usage(self):
        return self.__usages

    @property
    def UsageOverraped(self):
        return self.__usageOverraped

    def __str__(self):

        toStr = [self.__name,
                 ' Inputs:',
                 '\n'.join([f"  {x[1]} : {x[0]}" for x in self.__inputs]),
                 ' Outputs:',
                 '\n'.join([f"  {x[0]} for ({', '.join(x[1])})" for x in self.__outputs])
                 ]

        if len(self.__presets) > 0:
            presets = ', '.join(self.__presets)
            toStr.append(f' Presets: {presets}')

        if len(self.__usages) > 0:
            usages = ', '.join(self.__usages)
            toStr.append(f' Usages: {usages}')

        return '\n'.join(toStr)


class SBSARInfo(dict):
    def __init__(self, sbsarPath: str):
        super().__init__()
        self.__sbsarPath = Path(sbsarPath)
        installPath = Path(Context.getAutomationToolkitInstallPath())
        sbsrender_exe = installPath.joinpath("sbsrender.exe")
        sbsar = sbsarPath

        result: CompletedProcess = run([sbsrender_exe, "info", sbsar], capture_output=True,
                                       creationflags=CREATE_NO_WINDOW)
        infoByte = result.stdout.decode()
        infos = tuple(infoByte.strip().split('\r\n\r\n'))
        for g in infos:
            graphInfo = GraphInfo(g)
            self[graphInfo.Name] = graphInfo

    @property
    def GraphNames(self):
        return tuple(self.keys())

    @property
    def Graphs(self):
        return tuple(self.values())

    @property
    def Path(self) -> Path:
        return self.__sbsarPath

    def __str__(self):
        toStr = [f'SBSAR: {self.__sbsarPath}']
        for k, v in self.items():
            toStr.append(str(v))
        return '\n'.join(toStr)

    def __getitem__(self, item) -> GraphInfo:
        return super().__getitem__(item)


def GetSBSARInfo(sbsarPath: str):
    return SBSARInfo(sbsarPath)

    return sbsarInfo


if __name__ == '__main__':
    print(GetSBSARInfo(r"C:\test\presetTest.sbsar"))
