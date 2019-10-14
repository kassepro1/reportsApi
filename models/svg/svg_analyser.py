from xml.etree import ElementTree
import re, sys


class SvgAnalyser:
    """
    Get different information from a template (polylines, y top and y bottom)
    """
    def get_polylines(self, path):
        """
        Get the polylines contained in the SVG template
        :param path: path to the svg template
        :return: all the polylines contained in the SVG template 
        """
        tree = ElementTree.parse(path)
        polylines = tree.iter("{http://www.w3.org/2000/svg}polyline")
        return polylines

    def find_polylines(self, path):
        """
        Find all the polylines that aren't fully horizontal (where all the points have the same y)
        :param path: path to the SVG template
        :return: an array containing all the polylines
        """
        polylines = []
        all_polylines = self.get_polylines(path)

        for node in all_polylines:
            att_points = node.attrib.get("points")
            list_coordinate = []
            list_same_y_coordinate = []
            previous_y = -1

            regex = r"[, ]+"

            # Get the coordinate by removing the , and the space
            coordinates = re.split(regex, att_points)

            for j in range(0, len(coordinates), 2):
                if j + 1 < len(coordinates):
                    x = float(coordinates[j])
                    y = float(coordinates[j + 1])

                    # Verify that there isn't multiple point at the same y
                    previous_y = y if previous_y == -1 else previous_y
                    if y == previous_y:
                        list_same_y_coordinate.append(y)

                    list_coordinate.append((x, y))

            # Add the list of coordinate if they aren't all on the same line
            if len(list_same_y_coordinate) != len(list_coordinate):
                polylines.append(list_coordinate)

        return polylines

    def get_boundaries(self, polylines):
        """
        Get the lowest and highest point of the pylon (y axis)
        :param polylines: list of polyline [list of coordinates (x,y)]
        :return: the lowest and highest y coordinate
        """
        y_min = sys.maxsize
        y_max = -1

        for polyline in polylines:
            min_poly = min(polyline, key=lambda t: t[1]) # Get the tuple that contains the lowest y coordinate
            max_poly = max(polyline, key=lambda t: t[1]) # Get the tuple that contains the highest y coordinate
            y_min = min(min_poly[1], y_min)
            y_max = max(max_poly[1], y_max)

        return y_min, y_max

