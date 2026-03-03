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

    def _export_points(self):
        print('Exporting points')
        points_folder = os.path.join(self.output_folder_path, self.out_folder_name, 'points')
        os.mkdir(points_folder)

        # query all POINT entities
        points = self.msp.query("POINT")

        # check present layers
        layers = []
        for point in points:
            layer = point.dxf.layer
            if layer not in layers:
                layers.append(layer)
        # print(layers)

        # classify points by layer and save
        for layer in layers:
            layer_dict = {
                'type': [], 
                'geometry': []
            }

            count = 0
            for point in points:
                if point.dxf.layer == layer:
                    x, y, z = point.dxf.location
                    # print(f"found point in {layer} at {x} {y}")
                    layer_dict['type'].append('POINT')
                    layer_dict['geometry'].append(Point(x, y))
                    count += 1
            print(f"\tExporting {count} points in layer {layer}")

            gdf = gpd.GeoDataFrame(layer_dict)
            gdf.to_file(os.path.join(points_folder, f"{layer}.shp"))
        
        print(green('\tExported'))

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

        # lines, polylines, arcs
        lines_folder = os.path.join(self.output_folder_path, self.out_folder_name, 'lines')
        os.mkdir(lines_folder)

        # query all LINE, POLYLINES, ARC entities
        lines = self.msp.query("LINE")
        lwpolylines = self.msp.query("LWPOLYLINE")
        polylines = self.msp.query("POLYLINE")
        arcs = self.msp.query("ARC")

        # check present layers
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
        # print(layers)

        # classify lines by layer and save
        for layer in layers:
            layer_dict = {
                'type': [], 
                'geometry': []
            }

            count = 0
            for line in lines:
                if line.dxf.layer == layer:
                    start = line.dxf.start
                    end = line.dxf.end
                    # print(f"found line in {layer} at {start.x} {start.y}")
                    layer_dict['type'].append('LINE')
                    layer_dict['geometry'].append(LineString([[start.x, start.y], [end.x, end.y]]))
                    count += 1

            for lwpline in lwpolylines:
                if lwpline.dxf.layer == layer:
                    vertices = []
                    for x, y, *_ in lwpline.get_points():  # returns (x, y, [start_width, end_width, bulge])
                        vertices.append([float(x), float(y)])
                    if lwpline.closed and vertices[0] != vertices[-1]:
                        vertices.append(vertices[0])

                    # print(f"found lwpolyline in {layer} at {vertices}")
                    layer_dict['type'].append('LWPOLYLINE')
                    layer_dict['geometry'].append(LineString(vertices))
                    count += 1

            for pline in polylines:
                if pline.dxf.layer == layer:
                    vertices = []
                    for vertex in pline.vertices:
                        x, y, z = vertex.dxf.location
                        vertices.append([float(x), float(y)])
                    if pline.is_closed and vertices[0] != vertices[-1]:
                        vertices.append(vertices[0])
                    # print(f"found polyline in {layer}")
                    layer_dict['type'].append('POLYLINE')
                    layer_dict['geometry'].append(LineString(vertices))
                    count += 1

            for arc in arcs:
                if arc.dxf.layer == layer:
                    vertices = self.__arc_to_linestring(arc)
                    # print(f"found arc in {layer} at {vertices}")
                    layer_dict['type'].append('ARC')
                    layer_dict['geometry'].append(LineString(vertices))
                    count += 1
            
            print(f"\tExporting {count} lines in layer {layer}")

            gdf = gpd.GeoDataFrame(layer_dict)
            gdf.to_file(os.path.join(lines_folder, f"{layer}.shp"))

        print(green('\tExported'))

    def _export_texts(self):
        print('Exporting texts')
        # texts, mtexts
        texts_folder = os.path.join(self.output_folder_path, self.out_folder_name, 'texts')
        os.mkdir(texts_folder)

        # query all TEXT, MTEXT entities
        texts = self.msp.query("TEXT")
        mtexts = self.msp.query("MTEXT")

        # check present layers
        layers = []
        for text in texts:
            layer = text.dxf.layer
            if layer not in layers:
                layers.append(layer)
        for mtext in mtexts:
            layer = mtext.dxf.layer
            if layer not in layers:
                layers.append(layer)
        # print(layers)

        # classify points by layer and save
        for layer in layers:
            layer_dict = {
                'type': [], 
                'content': [],
                'geometry': []
            }

            count = 0
            for text in texts:
                if text.dxf.layer == layer:
                    insert = text.dxf.insert
                    content = text.dxf.text
                    layer_dict['type'].append('TEXT')
                    layer_dict['content'].append(content)
                    layer_dict['geometry'].append(Point(insert.x, insert.y))
                    count += 1

            for mtext in mtexts:
                if mtext.dxf.layer == layer:
                    insert = mtext.dxf.insert
                    content = mtext.plain_text()
                    layer_dict['type'].append('MTEXT')
                    layer_dict['content'].append(content)
                    layer_dict['geometry'].append(Point(insert.x, insert.y))
                    count += 1

            print(f"\tExporting {count} texts in layer {layer}")

            gdf = gpd.GeoDataFrame(layer_dict)
            gdf.to_file(os.path.join(texts_folder, f"{layer}.shp"))

        print(green('\tExported'))

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

        # query all CIRCLE entities
        circles = self.msp.query("CIRCLE")

        # check present layers
        layers = []
        for circle in circles:
            layer = circle.dxf.layer
            if layer not in layers:
                layers.append(layer)
        # print(layers)

        # classify circles by layer and save
        for layer in layers:
            layer_dict = {
                'type': [], 
                'geometry': []
            }

            count = 0
            for circle in circles:
                if circle.dxf.layer == layer:
                    vertices = self.__circle_to_polygon(circle)
                    layer_dict['type'].append('CIRCLE')
                    layer_dict['geometry'].append(LineString(vertices))
                    count += 1

            print(f"\tExporting {count} circles in layer {layer}")

            gdf = gpd.GeoDataFrame(layer_dict)
            gdf.to_file(os.path.join(circles_folder, f"{layer}.shp"))

        print(green('\tExported'))

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
        
        # Reserved Words: Avoid using reserved keywords that may conflict with SQL or the specific GIS software being used
        # Uniqueness: Field names must be unique within the shapefile.

        return block_attr

    def _export_blocks(self):
        print('Exporting blocks')
        blocks_folder = os.path.join(self.output_folder_path, self.out_folder_name, 'blocks')
        os.mkdir(blocks_folder)

        # query all INSERT entities
        blocks = self.msp.query("INSERT")

        # check present layers
        layers = []
        for block in blocks:
            layer = block.dxf.layer
            if layer not in layers:
                layers.append(layer)
        # print(layers)

        # classify blocks by layer and save
        for layer in layers:
            layer_dict = {
                'type': [], 
                'block_name': [],
                'geometry': []
            }
            # collect attributes names
            for block in blocks:
                if block.dxf.layer == layer:
                    if block.attribs:
                        for attrib in block.attribs:
                            block_attr = attrib.dxf.tag  # block attrib name
                            valid_column = self.__get_valid_shp_column_name(block_attr)
                            if valid_column not in list(layer_dict.keys()):
                                layer_dict[valid_column] = []
            
            count = 0
            for block in blocks:
                if block.dxf.layer == layer:
                    block_name = block.dxf.name
                    x, y, z = block.dxf.insert

                    layer_dict['type'].append('INSERT')
                    layer_dict['block_name'].append(block_name)
                    layer_dict['geometry'].append(Point(x, y))
                    for col in list(layer_dict.keys()):  # insert None values first to avoid falling behind
                        if col not in ['type', 'block_name', 'geometry']:
                            layer_dict[col].append(None)

                    if block.attribs:
                        for attrib in block.attribs:
                            block_attr = attrib.dxf.tag  # block attrib name
                            text_value = attrib.dxf.text  # block text content

                            valid_column = self.__get_valid_shp_column_name(block_attr)
                            layer_dict[valid_column][-1] = text_value

                    count += 1

            print(f"\tExporting {count} blocks in layer {layer}")

            gdf = gpd.GeoDataFrame(layer_dict)
            gdf.to_file(os.path.join(blocks_folder, f"{layer}.shp"))

        print(green('\tExported'))

    def _export_report(self):
        pass

    def run(self):
        functions = [
            self._read_dxf,
            self._create_out_folder,
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
