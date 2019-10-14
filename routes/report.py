import _pickle as pickle
import os
from flask import current_app, Blueprint, request, render_template, session, jsonify, url_for, redirect
from flagshipcore.flagship.libserver import QualiticsFlagship, MissionOpenMode, QualiticsFlagshipException

from models.constants import MISSION_KEY
from models.messages_manager import get_msg_manager
from models.svg.svg_manager import SvgManager
report_bp = Blueprint('report', __name__)


def create_qflagship():
    return QualiticsFlagship(current_app.config['FLAGSHIP_SERVER'])


@report_bp.route('/report/<string:mission_id>', methods=["GET"])
def display(mission_id):
    """Render the report page depending on type of the selected mission"""
    rest = create_qflagship()
    token = request.cookies.get('token')
    svg_data = {}
    photos_to_display = []
    photos_info = []
    msg_manager = get_msg_manager()
    msg_manager.messages = []
    json_obj = {}
    qmission = None

    if token is not None and rest.authenticated(token):
        # Afficher en dessous la liste avec toutes les missions, pouvoir sélectionner une et générer le svg

        try:
            missions = rest.adm_get_missions()
            qmission = [m for m in missions if m.id == int(mission_id)][0]

            # save mission in session to access data later
            to_save_mission = pickle.dumps(qmission)
            session[MISSION_KEY] = to_save_mission
        except (QualiticsFlagshipException, Exception) as ex:
            msg_manager.append_error(ex)
            if session.get(MISSION_KEY) is not None:
                session.pop(MISSION_KEY)

        # If no mission can be found, return to selection page
        if session.get(MISSION_KEY) is None or qmission is None:
            return redirect(url_for('home.show'))

        # call method to begin generation : give qmission, paths
        svg_manager = SvgManager()

        try:
            json_obj = rest.adm_get_report_data(qmission).data
        except QualiticsFlagshipException as ex:
            msg_manager.append_error(ex)

        try:
            photos_info = rest.com_get_mission_photos(qmission)
        except QualiticsFlagshipException as ex:
            msg_manager.append_error(ex)

        if len(photos_info) > 0:
            svg_data, photos_to_display = svg_manager.generate_report(photos_info, json_obj)

    return render_template("svg_display.html", data=svg_data, images=photos_to_display, messages=msg_manager.messages)


@report_bp.route('/report/save', methods=["POST"])
def save():
    rest = create_qflagship()
    token = request.cookies.get('token')
    msg_manager = get_msg_manager()

    if token is not None and rest.authenticated(token):
        # Get selected mission saved in session
        mission = pickle.loads(session[MISSION_KEY])

        try:
            json_obj = rest.adm_get_report_data(mission).data

            # If json object is not empty, send data to flagship
            if json_obj:
                rest.adm_open_mission(mission, MissionOpenMode.MODE_PROCESSING)
                print("Mission send for processing.")
        except QualiticsFlagshipException as ex:
            msg_manager.append_error(ex)

    return redirect(url_for("home.show"))


@report_bp.route('/report/photoID/<int:photo_id>', methods=["GET"])
def get_cached_image(photo_id):
    rest = create_qflagship()
    token = request.cookies.get('token')
    msg_manager = get_msg_manager()

    tmp_folder = current_app.config["FOLDER_TMP"]
    tmp_path = os.path.join(current_app.config["STATIC_FOLDER"], tmp_folder)

    # Check if tmp folder exist, if not create it
    if not os.path.exists(tmp_path):
        os.makedirs(tmp_path)

    # Path for cached img :
    img_name = "{}.jpeg".format(photo_id)
    img_path = os.path.join(tmp_path, img_name)

    filename = os.path.join(tmp_folder, img_name)

    # If not in cache, request image
    if not os.path.isfile(img_path):
        if token is not None and rest.authenticated(token):
            # Get selected mission saved in session
            mission = pickle.loads(session[MISSION_KEY])

            # Find photo info from rest service
            qphotos = rest.com_get_mission_photos(mission)
            photo_info = [photo for photo in qphotos if photo.id == int(photo_id)][0]

            # Get raw image from rest service and save in cache
            img_scale = float(current_app.config["IMG_SCALE"])
            try:
                raw_image = rest.com_get_photo(photo_info, img_scale)

                with open(img_path, "wb") as fh:
                    fh.write(raw_image)

            except QualiticsFlagshipException as ex:
                filename = os.path.join(current_app.config['FOLDER_ASSETS'], 'not-available.png')

    photo_data = {"id": photo_id, "path": url_for('static', filename=filename)}

    return jsonify(photo_data)
