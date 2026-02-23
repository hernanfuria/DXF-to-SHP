import ezdxf
import geopandas as gpd
from shapely import Point, LineString

import os
from datetime import datetime
import math

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
        self.out_folder_name = f"{self.dxf_file_name[:-4]}_{now.year}{now.month}{now.day}_{now.hour}{now.minute}{now.second}"
        os.mkdir(os.path.join(self.output_folder_path, self.out_folder_name))

    def _export_points(self):
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

            for point in points:
                if point.dxf.layer == layer:
                    x, y, z = point.dxf.location
                    # print(f"found point in {layer} at {x} {y}")
                    layer_dict['type'].append('POINT')
                    layer_dict['geometry'].append(Point(x, y))

            gdf = gpd.GeoDataFrame(layer_dict)
            gdf.to_file(os.path.join(points_folder, f"{layer}.shp"))

    def __arc_to_linestring(self, arc):
        center = arc.dxf.center
        radius = arc.dxf.radius
        start_angle = arc.dxf.start_angle
        end_angle = arc.dxf.end_angle
        print(center, radius, start_angle, end_angle)

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

            for line in lines:
                if line.dxf.layer == layer:
                    start = line.dxf.start
                    end = line.dxf.end
                    # print(f"found line in {layer} at {start.x} {start.y}")
                    layer_dict['type'].append('LINE')
                    layer_dict['geometry'].append(LineString([[start.x, start.y], [end.x, end.y]]))

            for lwpline in lwpolylines:
                if lwpline.dxf.layer == layer:
                    vertices = []
                    for x, y, *_ in lwpline.get_points():  # returns (x, y, [start_width, end_width, bulge])
                        vertices.append([float(x), float(y)])
                    # print(f"found lwpolyline in {layer} at {vertices}")
                    layer_dict['type'].append('LWPOLYLINE')
                    layer_dict['geometry'].append(LineString(vertices))

            for pline in polylines:
                if pline.dxf.layer == layer:
                    vertices = []
                    for vertex in pline.vertices:
                        x, y, z = vertex.dxf.location
                        vertices.append([float(x), float(y)])
                    # print(f"found polyline in {layer}")
                    layer_dict['type'].append('POLYLINE')
                    layer_dict['geometry'].append(LineString(vertices))

            for arc in arcs:
                if arc.dxf.layer == layer:
                    vertices = self.__arc_to_linestring(arc)
                    # print(f"found arc in {layer} at {vertices}")
                    layer_dict['type'].append('ARC')
                    layer_dict['geometry'].append(LineString(vertices))

            gdf = gpd.GeoDataFrame(layer_dict)
            gdf.to_file(os.path.join(lines_folder, f"{layer}.shp"))

    def _export_texts(self):
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

            for text in texts:
                if text.dxf.layer == layer:
                    insert = text.dxf.insert
                    content = text.dxf.text
                    layer_dict['type'].append('TEXT')
                    layer_dict['content'].append(content)
                    layer_dict['geometry'].append(Point(insert.x, insert.y))

            for mtext in mtexts:
                if mtext.dxf.layer == layer:
                    insert = mtext.dxf.insert
                    content = mtext.plain_text()
                    layer_dict['type'].append('MTEXT')
                    layer_dict['content'].append(content)
                    layer_dict['geometry'].append(Point(insert.x, insert.y))

            gdf = gpd.GeoDataFrame(layer_dict)
            gdf.to_file(os.path.join(texts_folder, f"{layer}.shp"))

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

            for circle in circles:
                if circle.dxf.layer == layer:
                    vertices = self.__circle_to_polygon(circle)
                    layer_dict['type'].append('CIRCLE')
                    layer_dict['geometry'].append(LineString(vertices))

            gdf = gpd.GeoDataFrame(layer_dict)
            gdf.to_file(os.path.join(circles_folder, f"{layer}.shp"))

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
            self._export_points,
            self._export_lines,
            self._export_texts,
            self._export_circles,
            # self._export_mleaders,
            # self._export_blocks,
            # self._export_report,
        ]

        for f in functions:
            try:
                f()
            except Exception:
                print(red(f"Failed while running {f.__name__}"))
