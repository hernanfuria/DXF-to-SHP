import warnings
warnings.filterwarnings('ignore')

import ezdxf
import geopandas as gpd
from shapely import Point, LineString

import os
from datetime import datetime
import math
import string

from clic import red, green


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

        self.reproject = False
        self.input_crs = 0
        self.output_crs = 0

    def _read_dxf(self):
        print(f"Reading {os.path.join(self.input_folder_path, self.dxf_file_name)}")
        self.dxf = ezdxf.readfile(os.path.join(self.input_folder_path, self.dxf_file_name))
        self.msp = self.dxf.modelspace()
        print(green('\tDrawing read'))

    def __double_digit_number(self, number) -> str:
        num_str = str(number)
        if len(num_str) == 1:
            return '0' + num_str
        
        return num_str

    def _create_out_folder(self):
        print('Creating output folder')
        now = datetime.now()
        year = self.__double_digit_number(now.year)
        month = self.__double_digit_number(now.month)
        day = self.__double_digit_number(now.day)
        hour = self.__double_digit_number(now.hour)
        minute = self.__double_digit_number(now.minute)
        second = self.__double_digit_number(now.second)
        self.out_folder_name = f"{self.dxf_file_name[:-4]}_{year}{month}{day}_{hour}{minute}{second}"
        os.mkdir(os.path.join(self.output_folder_path, self.out_folder_name))
        print(green(f"\t{os.path.join(self.output_folder_path, self.out_folder_name)} created"))

    def _get_reproject_info(self):
        self.reproject = False
        self.input_crs = 0
        self.output_crs = 0

        rep = input('Do you want to export in a specific CRS? (y/n): ')
        if rep in ['y', 'Y', 'yes', 'Yes', 'YES']:
            self.reproject = True
            input_crs = input("What's the autocad drawing CRS? (please enter just the number, for example: 22195): ")
            self.input_crs = int(input_crs)
            output_crs = input("What CRS do you want the shapefiles to be?: ")
            self.output_crs = int(output_crs)

    def __create_and_export_shp(self, layer_dict: dict, output_path: str):
        if self.reproject:
            gdf = gpd.GeoDataFrame(layer_dict)
            gdf = gdf.set_crs(epsg=self.input_crs)
            gdf = gdf.to_crs(epsg=self.output_crs)
            gdf.to_file(output_path)
        else:
            gdf = gpd.GeoDataFrame(layer_dict)
            gdf.to_file(output_path)

    def _export_points(self):
        print('Exporting points')
        points_folder = os.path.join(self.output_folder_path, self.out_folder_name, 'points')
        os.mkdir(points_folder)

        # Query all POINT entities
        points = self.msp.query("POINT")

        # Check present layers
        layers = []
        for point in points:
            layer = point.dxf.layer
            if layer not in layers:
                layers.append(layer)

        # Classify points by layer and save with robust element-level error handling
        for layer in layers:
            print(f"\tExporting layer '{layer}'...")
            layer_dict = {
                'type': [], 
                'geometry': []
            }

            count = 0
            error_count = 0
            for point in points:
                if point.dxf.layer == layer:
                    try:
                        x, y, z = point.dxf.location
                        layer_dict['type'].append('POINT')
                        layer_dict['geometry'].append(Point(x, y))
                        count += 1
                    except Exception as e:
                        error_count += 1
                        print(red(f"\t\t[Error] Failed to process point element in layer '{layer}': {e}"))

            if count > 0:
                try:
                    self.__create_and_export_shp(layer_dict=layer_dict, output_path=os.path.join(points_folder, f"{layer}.shp"))
                    print(green(f"\t\tSuccessfully exported {count} points in layer '{layer}' (Errors: {error_count})"))
                except Exception as e:
                    print(red(f"\t\t[Error] Failed to save shapefile for points in layer '{layer}': {e}"))
            else:
                print(f"\t\tNo valid points found to export in layer '{layer}' (Errors: {error_count})")
        
        print(green('\tExported points completed'))

    def __arc_to_linestring(self, arc):
        center = arc.dxf.center
        radius = arc.dxf.radius
        start_angle = arc.dxf.start_angle
        end_angle = arc.dxf.end_angle

        # Normalize sweep
        if end_angle < start_angle:
            end_angle += 360

        sweep = end_angle - start_angle
        segments = int(sweep)

        vertices = []

        for i in range(segments + 1):
            angle_deg = start_angle + sweep * (i / segments)
            angle_rad = math.radians(angle_deg)

            x = center.x + radius * math.cos(angle_rad)
            y = center.y + radius * math.sin(angle_rad)

            vertices.append([x, y])

        return vertices

    def _export_lines(self):
        print('Exporting lines')

        # Lines, polylines, arcs
        lines_folder = os.path.join(self.output_folder_path, self.out_folder_name, 'lines')
        os.mkdir(lines_folder)

        # Query all LINE, LWPOLYLINE, POLYLINE, ARC entities
        lines = self.msp.query("LINE")
        lwpolylines = self.msp.query("LWPOLYLINE")
        polylines = self.msp.query("POLYLINE")
        arcs = self.msp.query("ARC")

        # Check present layers
        layers = []
        for line in lines:
            layer = line.dxf.layer
            if layer not in layers:
                layers.append(layer)
        for lwpline in lwpolylines:
            layer = lwpline.dxf.layer
            if layer not in layers:
                layers.append(layer)
        for pline in polylines:
            layer = pline.dxf.layer
            if layer not in layers:
                layers.append(layer)
        for arc in arcs:
            layer = arc.dxf.layer
            if layer not in layers:
                layers.append(layer)

        # Classify lines by layer and save with robust element-level error handling
        for layer in layers:
            print(f"\tExporting layer '{layer}'...")
            layer_dict = {
                'type': [], 
                'geometry': []
            }

            count = 0
            error_count = 0

            for line in lines:
                if line.dxf.layer == layer:
                    try:
                        start = line.dxf.start
                        end = line.dxf.end
                        layer_dict['type'].append('LINE')
                        layer_dict['geometry'].append(LineString([[start.x, start.y], [end.x, end.y]]))
                        count += 1
                    except Exception as e:
                        error_count += 1
                        print(red(f"\t\t[Error] Failed to process LINE in layer '{layer}': {e}"))

            for lwpline in lwpolylines:
                if lwpline.dxf.layer == layer:
                    try:
                        vertices = []
                        for x, y, *_ in lwpline.get_points():
                            vertices.append([float(x), float(y)])
                        if lwpline.closed and vertices and vertices[0] != vertices[-1]:
                            vertices.append(vertices[0])
                        if vertices:
                            layer_dict['type'].append('LWPOLYLINE')
                            layer_dict['geometry'].append(LineString(vertices))
                            count += 1
                    except Exception as e:
                        error_count += 1
                        print(red(f"\t\t[Error] Failed to process LWPOLYLINE in layer '{layer}': {e}"))

            for pline in polylines:
                if pline.dxf.layer == layer:
                    try:
                        vertices = []
                        for vertex in pline.vertices:
                            x, y, z = vertex.dxf.location
                            vertices.append([float(x), float(y)])
                        if pline.is_closed and vertices and vertices[0] != vertices[-1]:
                            vertices.append(vertices[0])
                        if vertices:
                            layer_dict['type'].append('POLYLINE')
                            layer_dict['geometry'].append(LineString(vertices))
                            count += 1
                    except Exception as e:
                        error_count += 1
                        print(red(f"\t\t[Error] Failed to process POLYLINE in layer '{layer}': {e}"))

            for arc in arcs:
                if arc.dxf.layer == layer:
                    try:
                        vertices = self.__arc_to_linestring(arc)
                        if vertices:
                            layer_dict['type'].append('ARC')
                            layer_dict['geometry'].append(LineString(vertices))
                            count += 1
                    except Exception as e:
                        error_count += 1
                        print(red(f"\t\t[Error] Failed to process ARC in layer '{layer}': {e}"))
            
            if count > 0:
                try:
                    self.__create_and_export_shp(layer_dict=layer_dict, output_path=os.path.join(lines_folder, f"{layer}.shp"))
                    print(green(f"\t\tSuccessfully exported {count} lines/curves in layer '{layer}' (Errors: {error_count})"))
                except Exception as e:
                    print(red(f"\t\t[Error] Failed to save shapefile for lines in layer '{layer}': {e}"))
            else:
                print(f"\t\tNo valid lines found to export in layer '{layer}' (Errors: {error_count})")

        print(green('\tExported lines completed'))

    def _export_texts(self):
        print('Exporting texts')
        texts_folder = os.path.join(self.output_folder_path, self.out_folder_name, 'texts')
        os.mkdir(texts_folder)

        # Query all TEXT, MTEXT entities
        texts = self.msp.query("TEXT")
        mtexts = self.msp.query("MTEXT")

        # Check present layers
        layers = []
        for text in texts:
            layer = text.dxf.layer
            if layer not in layers:
                layers.append(layer)
        for mtext in mtexts:
            layer = mtext.dxf.layer
            if layer not in layers:
                layers.append(layer)

        # Classify texts by layer and save with robust element-level error handling
        for layer in layers:
            print(f"\tExporting layer '{layer}'...")
            layer_dict = {
                'type': [], 
                'content': [],
                'geometry': []
            }

            count = 0
            error_count = 0

            for text in texts:
                if text.dxf.layer == layer:
                    try:
                        insert = text.dxf.insert
                        content = text.dxf.text
                        layer_dict['type'].append('TEXT')
                        layer_dict['content'].append(content)
                        layer_dict['geometry'].append(Point(insert.x, insert.y))
                        count += 1
                    except Exception as e:
                        error_count += 1
                        print(red(f"\t\t[Error] Failed to process TEXT in layer '{layer}': {e}"))

            for mtext in mtexts:
                if mtext.dxf.layer == layer:
                    try:
                        insert = mtext.dxf.insert
                        content = mtext.plain_text()
                        layer_dict['type'].append('MTEXT')
                        layer_dict['content'].append(content)
                        layer_dict['geometry'].append(Point(insert.x, insert.y))
                        count += 1
                    except Exception as e:
                        error_count += 1
                        print(red(f"\t\t[Error] Failed to process MTEXT in layer '{layer}': {e}"))

            if count > 0:
                try:
                    self.__create_and_export_shp(layer_dict=layer_dict, output_path=os.path.join(texts_folder, f"{layer}.shp"))
                    print(green(f"\t\tSuccessfully exported {count} texts in layer '{layer}' (Errors: {error_count})"))
                except Exception as e:
                    print(red(f"\t\t[Error] Failed to save shapefile for texts in layer '{layer}': {e}"))
            else:
                print(f"\t\tNo valid texts found to export in layer '{layer}' (Errors: {error_count})")

        print(green('\tExported texts completed'))

    def __circle_to_polygon(self, circle, segments=360):
        center = circle.dxf.center
        radius = circle.dxf.radius

        vertices = []

        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = center.x + radius * math.cos(angle)
            y = center.y + radius * math.sin(angle)
            vertices.append((x, y))

        # Close the ring
        vertices.append(vertices[0])

        return vertices

    def _export_circles(self):
        print('Exporting circles')
        circles_folder = os.path.join(self.output_folder_path, self.out_folder_name, 'circles')
        os.mkdir(circles_folder)

        # Query all CIRCLE entities
        circles = self.msp.query("CIRCLE")

        # Check present layers
        layers = []
        for circle in circles:
            layer = circle.dxf.layer
            if layer not in layers:
                layers.append(layer)

        # Classify circles by layer and save with robust element-level error handling
        for layer in layers:
            print(f"\tExporting layer '{layer}'...")
            layer_dict = {
                'type': [], 
                'geometry': []
            }

            count = 0
            error_count = 0
            for circle in circles:
                if circle.dxf.layer == layer:
                    try:
                        vertices = self.__circle_to_polygon(circle)
                        layer_dict['type'].append('CIRCLE')
                        layer_dict['geometry'].append(LineString(vertices))
                        count += 1
                    except Exception as e:
                        error_count += 1
                        print(red(f"\t\t[Error] Failed to process CIRCLE in layer '{layer}': {e}"))

            if count > 0:
                try:
                    self.__create_and_export_shp(layer_dict=layer_dict, output_path=os.path.join(circles_folder, f"{layer}.shp"))
                    print(green(f"\t\tSuccessfully exported {count} circles in layer '{layer}' (Errors: {error_count})"))
                except Exception as e:
                    print(red(f"\t\t[Error] Failed to save shapefile for circles in layer '{layer}': {e}"))
            else:
                print(f"\t\tNo valid circles found to export in layer '{layer}' (Errors: {error_count})")

        print(green('\tExported circles completed'))

    def _export_mleaders(self):
        pass

    def __get_valid_shp_column_name(self, block_attr: str) -> str:
        # Allowed Characters: Must only contain alphanumeric characters (a-z, A-Z, 0-9) and the underscore (_)
        allowed_characters = list(string.ascii_letters + string.digits + '_')
        to_replace = []
        for character in block_attr:
            if character not in allowed_characters:
                to_replace.append(character)
        for character in to_replace:
            block_attr = block_attr.replace(character, '_')

        # Starting Character: Must begin with a letter, not a number or an underscore.
        if block_attr[0] not in list(string.ascii_letters):
            block_attr = 'a' + block_attr
        
        # Length: Maximum of 10 characters
        if len(block_attr) > 10:
            block_attr = block_attr[0:10]

        return block_attr

    def _export_blocks(self):
        print('Exporting blocks')
        blocks_folder = os.path.join(self.output_folder_path, self.out_folder_name, 'blocks')
        os.mkdir(blocks_folder)

        # Query all INSERT entities
        blocks = self.msp.query("INSERT")

        # Check present layers
        layers = []
        for block in blocks:
            layer = block.dxf.layer
            if layer not in layers:
                layers.append(layer)

        # Classify blocks by layer and save with robust element-level error handling
        for layer in layers:
            print(f"\tExporting layer '{layer}'...")
            layer_dict = {
                'type': [], 
                'block_name': [],
                'geometry': []
            }
            
            # Collect attribute names safely
            for block in blocks:
                if block.dxf.layer == layer:
                    try:
                        if block.attribs:
                            for attrib in block.attribs:
                                block_attr = attrib.dxf.tag  # block attrib name
                                valid_column = self.__get_valid_shp_column_name(block_attr)
                                if valid_column not in list(layer_dict.keys()):
                                    layer_dict[valid_column] = []
                    except Exception as e:
                        print(red(f"\t\t[Warning] Failed to inspect attributes for block in layer '{layer}': {e}"))

            count = 0
            error_count = 0
            for block in blocks:
                if block.dxf.layer == layer:
                    try:
                        block_name = block.dxf.name
                        x, y, z = block.dxf.insert

                        layer_dict['type'].append('INSERT')
                        layer_dict['block_name'].append(block_name)
                        layer_dict['geometry'].append(Point(x, y))
                        for col in list(layer_dict.keys()):  # Insert None values first to avoid falling behind
                            if col not in ['type', 'block_name', 'geometry']:
                                layer_dict[col].append(None)

                        if block.attribs:
                            for attrib in block.attribs:
                                try:
                                    block_attr = attrib.dxf.tag  # block attrib name
                                    text_value = attrib.dxf.text  # block text content

                                    valid_column = self.__get_valid_shp_column_name(block_attr)
                                    if valid_column in layer_dict:
                                        layer_dict[valid_column][-1] = text_value
                                except Exception as att_err:
                                    print(red(f"\t\t[Warning] Failed to process block attribute in layer '{layer}': {att_err}"))

                        count += 1
                    except Exception as e:
                        error_count += 1
                        print(red(f"\t\t[Error] Failed to process block instance in layer '{layer}': {e}"))

            if count > 0:
                try:
                    self.__create_and_export_shp(layer_dict=layer_dict, output_path=os.path.join(blocks_folder, f"{layer}.shp"))
                    print(green(f"\t\tSuccessfully exported {count} blocks in layer '{layer}' (Errors: {error_count})"))
                except Exception as e:
                    print(red(f"\t\t[Error] Failed to save shapefile for blocks in layer '{layer}': {e}"))
            else:
                print(f"\t\tNo valid blocks found to export in layer '{layer}' (Errors: {error_count})")

        print(green('\tExported blocks completed'))

    def _export_report(self):
        pass

    def run(self):
        functions = [
            self._read_dxf,
            self._create_out_folder,
            self._get_reproject_info,
            self._export_points,
            self._export_lines,
            self._export_texts,
            self._export_circles,
            # self._export_mleaders,
            self._export_blocks,
            # self._export_report,
        ]

        for f in functions:
            try:
                f()
            except Exception:
                print(red(f"Failed while running {f.__name__}"))
