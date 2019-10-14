from operator import attrgetter
from flask import current_app
from models.svg.svg_analyser import SvgAnalyser
from models.svg.svg_processor import SvgProcessor
import os


class SvgManager:

    def __init__(self):
        self.svg_analyser = SvgAnalyser()
        self.svg_processor = SvgProcessor()

    def generate_report(self, photos_info, json_obj):
        pylon_size, pylon_offset = self.get_full_size(photos_info)

        svg_datas = {}
        photos_by_sub = []
        category = []
        submissions = []
        template_folder = ""

        # TODO if pylon_size is negative, error
        if pylon_size <= 0 :
            return svg_datas, photos_by_sub

        for photo in photos_info:
            # Get complete list of submissions
            if photo.subm not in submissions:
                submissions.append(photo.subm)

            if photo.category not in category and photo.category != "":
                category.append(photo.category)

        category_number = len(category)

        # Find category of pylon (only one per mission of cracks type)
        if category_number > 1:
            print("Number of categories in the mission is {}, and contains values : {}".format(len(category), category))
            return svg_datas, photos_by_sub
        elif category_number == 1:
            category_folder = "{}".format(category[0].replace(" ", "_").lower())
            print("Category Folder : {}", category_folder)

            template_folder = os.path.join(current_app.config["FOLDER_TEMPLATES_SVG"], category_folder)

        for submission in submissions:
            # If for some reason no category was saved during mission, use default template
            if category_number == 0:
                svg_path = os.path.join(current_app.config["FOLDER_TEMPLATES_SVG"], current_app.config["DEFAULT_SVG"])
            else:
                svg_path = os.path.join(template_folder, "{}.svg".format(submission.replace(" ", "").lower()))
            print(svg_path)

            if os.path.exists(svg_path):
                qphotos = []

                # Get all photos for the current submission
                for photo in photos_info:
                    photos_by_sub.append((photo.id, photo))
                    if photo.subm == submission:
                        qphotos.append(photo)

                # Get the different polylines except the fully horizontal ones
                polylines = self.svg_analyser.find_polylines(svg_path)
                (y_top, y_bottom) = self.svg_analyser.get_boundaries(polylines)
                dy = y_bottom - y_top

                # The scale is made to get the scaled height from the database (for ex: 18 meters IRL => 580 pixels)
                scale = dy / pylon_size
                svg_data = self.svg_processor.build(svg_path, polylines, qphotos, scale, y_bottom, pylon_offset, json_obj)

                # TODO Add eventually annotations on svg (numbers, pylon base, ...)

                svg_datas[submission] = svg_data

        return svg_datas, photos_by_sub

    def get_full_size(self, photos_info):
        max_alt = max(photos_info, key=attrgetter('altitude')).altitude
        min_alt = min(photos_info, key=attrgetter('altitude')).altitude

        size = max_alt - min_alt
        offset = abs(min_alt)

        return float(size), float(offset)
