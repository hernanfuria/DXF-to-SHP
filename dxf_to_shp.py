import ezdxf

import os
from datetime import datetime

from clic import red


class DXFtoSHP:
    """"""

    def __init__(
            self,
            input_folder_path: str, 
            output_folder_path: str,
            dxf_file_name: str
    ):
        self.input_folder_path = input_folder_path
        self.output_folder_path = output_folder_path
        self.dxf_file_name = dxf_file_name

    def _read_dxf(self):
        self.dxf = ezdxf.readfile(os.path.join(self.input_folder_path, self.dxf_file_name))
        self.msp = self.dxf.modelspace()

    def _create_out_folder(self):
        now = datetime.now()
        out_folder_name = f"{self.dxf_file_name[:-4]}_{now.year}{now.month}{now.day}_{now.hour}{now.minute}{now.second}"
        os.mkdir(os.path.join(self.output_folder_path, out_folder_name))

    def _export_points(self):
        pass

    def _export_lines(self):
        # lines, polylines, arcs
        pass

    def _export_texts(self):
        # texts, mtexts
        pass

    def _export_mleaders(self):
        pass

    def _export_blocks(self):
        pass

    def _export_report(self):
        pass

    def run(self):
        functions = [
            self._read_dxf,
            self._create_out_folder,
            # self._export_points,
            # self._export_lines,
            # self._export_texts,
            # self._export_mleaders,
            # self._export_blocks,
            # self._export_report,
        ]

        for f in functions:
            try:
                f()
            except Exception:
                print(red(f"Failed while running {f.__name__}"))
