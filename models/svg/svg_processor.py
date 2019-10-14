from xml.etree import ElementTree
import sys


class SvgProcessor:
    """
        Modify the SVG templates by appending some elements inside of them
    """

    def build(self, path, polylines, qphotos, scale, y_bottom, pylon_offset, json_obj):
        """
        Create circles and append them to the specific SVG template
        :param path: path to the SVG template
        :param polylines: list of polyline [list of coordinates (x,y)]
        :param dict_images: dictionnary that associated the image ID and its height
        :param scale: the report between the real height and the SVG template one
        :param y_bottom: the lowest y coordinate in the SVG template
        :return: the modified SVG template as a String
        """
        ElementTree.register_namespace("", "http://www.w3.org/2000/svg")
        tree = ElementTree.parse(path)
        root = tree.getroot()
        img_forms = {}

        root.attrib["class"] = "svg-render"

        # Check if json object exist
        if "jsonform" in json_obj:
            img_forms = json_obj["jsonform"]

        for photo in qphotos:
            annotation = ""

            # Get data from json if exists
            if str(photo.id) in img_forms:
                img_form = img_forms[str(photo.id)]
                annotation = img_form["annotation"]

            y = y_bottom - ((float(photo.altitude) + pylon_offset) * float(scale))

            (coord_1, coord_2) = self.calculate_coord(polylines, y)

            # TODO why coords can be none ? which situation ?
            if coord_1 is not None and coord_2 is not None:
                # Take the enclosing coordinates and find the x thanks to the y (previously found)
                x = self.find_x_circle(coord_1, coord_2, y)

                # Add the circles at the defined coordinate in the SVG template
                circle_coordinate = (int(x), int(y))
                circle = self.create_circle(circle_coordinate, photo.id)
                root.append(circle)

                # Add text tag for annotations
                text = self.construct_text(circle_coordinate, annotation)
                root.append(text)

        return ElementTree.tostring(root).decode()

    def calculate_coord(self, polylines, y):
        """
        Find the enclosing coordinates around the y
        :param polylines: list of polyline [list of coordinates (x,y)]
        :param y: the scaled y (equivalent to the height of the photo on the SVG template)
        :return: the enclosing coordinate around the y
        """
        min_x_1 = sys.maxsize
        min_x_2 = sys.maxsize

        coord_1 = None
        coord_2 = None

        for polyline in polylines:

            # List of polyline that contains a y coordinate <= y (above in the template because the y axis begin at
            # the top and go to the bottom)
            sup_list = [i for i in polyline if i[1] <= y]

            # List of polyline that contains a y coordinate > y
            sub_list = [i for i in polyline if i[1] >= y]

            # Verify that there are some enclosing element (at least one above and one below)
            if len(sup_list) >= 1 and len(sub_list) >= 1:

                # Find 2 coordinates that are the closest to the left (with the lowest x coordinate)
                tmp_polyline = list(polyline)
                min_poly_1 = min(polyline, key=lambda t: t[0])
                tmp_polyline.remove(min_poly_1)
                min_poly_2 = min(tmp_polyline, key=lambda t: t[0])

                #Verify that the polyline is the closest to the left
                if min(min_x_1, min_poly_1[0]) != min_x_1 or min(min_x_2, min_poly_2[0]) != min_x_2:
                    min_x_1 = min_poly_1[0]
                    min_x_2 = min_poly_2[0]

                    # Get the enclosing coordinates: the nearest up/down the y coordinate
                    coord_1 = min(sub_list, key=lambda t: t[1])
                    coord_2 = max(sup_list, key=lambda t: t[1])

        return coord_1, coord_2

    def find_x_circle(self, coord_1, coord_2, y_circle):
        """
        Find the x coordinate thanks to 2 enclosing points and the y
        :param coord_1: enclosing coordinate (above)
        :param coord_2: enclosing coordinate (below)
        :param y_circle: the scaled y coordinate
        :return: the x coordinate
        """

        x_circle = coord_1[0]

        # Verify that the line is not vertical (same x coordinates)
        if coord_1[0] != coord_2[0]:
            # Find the gradient
            m = ((coord_2[1] - coord_1[1]) / (coord_2[0] - coord_1[0]))

            # Find the origin
            p = coord_1[1] - (m * coord_1[0])

            # Find x via equation and y
            x_circle = (y_circle - p) / m

        return x_circle

    def construct_text(self, circle_coordinate, annotation):
        tag = '<text text-anchor="end" dominant-baseline="middle" stroke="black" font-size="12">{}</text>'\
            .format(annotation)
        text = ElementTree.XML(tag)
        text.attrib["x"] = str(circle_coordinate[0])
        text.attrib["y"] = str(circle_coordinate[1])
        text.attrib["dx"] = "-10"

        return text

    def create_circle(self, circle_coordinate, image_id):
        """
        Construct the SVG element: circle with the right coordinates and link to the image
        :param circle_coordinate: coordinates (x, y) for the circle
        :param image_id: identifier of the image (used in span tag to make the image appear)
        :return: the circle SVG element
        """
        circle = ElementTree.XML(
            '<circle r="3" stroke="green" stroke-width="1" fill="green" fill-opacity="0.4" class="tooltip" />')

        circle.attrib["cx"] = str(circle_coordinate[0])
        circle.attrib["cy"] = str(circle_coordinate[1])
        circle.attrib["data-tooltip-content"] = "#{}".format(image_id)
        return circle

    def append_sub_elements(self, svg_data, path, analyser):
        """
        Append the different sub-elements (base and numbers for enclosing faces) to the main SVG templates
        :param svg_data: main SVG template
        :param path: path to get the sub-elements
        :return: the modified SVG template with the sub-elements appended
        """
        ElementTree.register_namespace("", "http://www.w3.org/2000/svg")
        root = ElementTree.fromstring(svg_data)
        polylines = analyser.get_polylines(path)

        for polyline in polylines:
            polyline.attrib["stroke"] = "black"
            polyline.attrib["stroke-width"] = "1"
            root.append(polyline)

        return ElementTree.tostring(root).decode()