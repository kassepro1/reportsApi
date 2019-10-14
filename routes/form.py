import _pickle as pickle
from flask import current_app, Blueprint, request, render_template, session, redirect, url_for
from flagshipcore.flagship.libserver import QualiticsFlagship, MissionOpenMode, QualiticsFlagshipException, \
    MissionStatus, RESOURCE_NOT_FOUND

from models.constants import MISSION_KEY, JSON_FIRST_KEY, IMG_KEY
from models.messages_manager import get_msg_manager

form_bp = Blueprint('form', __name__)


def create_qflagship():
    return QualiticsFlagship(current_app.config['FLAGSHIP_SERVER'])


@form_bp.route('/form/<img_id>', methods=["GET"])
def display(img_id):
    img_form = []
    token = request.cookies.get('token')
    rest = create_qflagship()
    msg_manager = get_msg_manager()
    msg_manager.messages = []
    json_obj = {}

    # Convert to string
    img_id = str(img_id)

    # Save id in session to access it later
    session[IMG_KEY] = img_id

    mission = pickle.loads(session[MISSION_KEY])

    if token is not None and rest.authenticated(token):
        try:
            json_obj = rest.adm_get_report_data(mission).data
        except QualiticsFlagshipException as ex:
            if ex.unikeycode != RESOURCE_NOT_FOUND:
                msg_manager.append_error(ex)

        # Check if json object exist
        if JSON_FIRST_KEY in json_obj:
            json_obj = json_obj[JSON_FIRST_KEY]

        # Display in textfield previous value (if not empty)
        if img_id in json_obj:
            img_form = json_obj[img_id]

    return render_template("form.html", img_form=img_form, messages=msg_manager.messages)


@form_bp.route('/form/save', methods=["POST"])
def save():
    # Get value from form
    annotation = request.form["annotation"]
    img_id = session[IMG_KEY]
    mission = pickle.loads(session[MISSION_KEY])
    token = request.cookies.get('token')
    rest = create_qflagship()
    msg_manager = get_msg_manager()
    json_obj = {}

    if token is not None and rest.authenticated(token):
        try:
            json_obj = rest.adm_get_report_data(mission).data
        except QualiticsFlagshipException as ex:
            if ex.unikeycode != RESOURCE_NOT_FOUND:
                msg_manager.append_error(ex)

        # If json file doesn't exist, the initial key must be specified
        if not json_obj:
            json_obj[JSON_FIRST_KEY] = {}

        # If not empty, save value in json file
        if len(annotation) > 0 or img_id in json_obj[JSON_FIRST_KEY]:
            json_obj[JSON_FIRST_KEY][img_id] = {"annotation": annotation}

        try:
            # Send changes to Flagship Server
            if mission.status == MissionStatus.UPLOADED:
                rest.adm_open_mission(mission, MissionOpenMode.MODE_JSON)

            rest.adm_set_report_data(mission, json_obj)
        except QualiticsFlagshipException as ex:
            msg_manager.append_error(ex)

    return redirect(url_for('report.display', mission_id=mission.id))