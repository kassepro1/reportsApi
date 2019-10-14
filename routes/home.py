from flask import current_app, Blueprint, request, render_template, redirect, url_for, session, jsonify
from flagshipcore.flagship.libserver import QualiticsFlagship
from flagshipcore.flagship.codes import QualiticsFlagshipException
from models.forms import Form

home_bp = Blueprint('home', __name__)


def create_qflagship():
    return QualiticsFlagship(current_app.config['FLAGSHIP_SERVER'])


@home_bp.route('/', methods=["GET", "POST"])
def login():
    """Render the connexion page"""
    rest = create_qflagship()
    login_err = False
    error_msg = ""

    if request.method == 'POST':
        try:
            # Authenticate to flagship server
            if rest.authenticate(request.form["username"], request.form["password"], allow_customer=False):
                print("Authentication success. Redirect to home page")
                data = {
                    'token': rest.get_token(),
                    'username': request.form["username"],
                    'message': 'Authentication succes.'
                }

                return jsonify(data)
            else:
                print("Authentication failed.")
                login_err = True
                error_msg = "L'authentification a échoué. Veuillez indiquer votre identifiant et mot de passe."
        except QualiticsFlagshipException as ex:
            login_err = True
            error_msg = "Auth failed : %s".format(ex.error_body)

    token = request.cookies.get('token')

    # If request method is get, and user is always connected, redirect to main page
    if token is not None and rest.authenticated(token):
        data = {
            'token': '',
            'username': '',
            'message': 'Authentication failed.'
        }

        return jsonify(data)


@home_bp.route('/logout/<string:token>', methods=["GET", "POST"])
def logout(token):
    rest = create_qflagship()

    try:
        if token is not None and rest.authenticated(token):
            data = {
                'logout': 'OK'
            }
            return data
        else:
            data = {
                'logout': 'NOOK'
            }
            return jsonify(data)
    except QualiticsFlagshipException as ex:
        data = {
            'logout': 'NOOK'
        }
        return jsonify(data)



@home_bp.route('/index', methods=["GET", "POST"])
def show():
    # TODO select client and mission type + svg model
    rest = create_qflagship()
    token = request.cookies.get('token')
    form = Form()
    msg_manager = current_app.config['MSG_MANAGER']

    # Clear session in case mission was previously loaded
    session.clear()

    if request.method == 'GET':
        try:
            if token is not None and rest.authenticated(token):
                # Get missions from the Server to display them in the table view
                form.missions = rest.adm_get_missions()
            else:
                return redirect(url_for('home.login'))
        except QualiticsFlagshipException as ex:
            msg_manager.append_error(ex)

    return render_template("index.html", form=form, messages=msg_manager.messages)


@home_bp.route("/fg/delete/error/id/<message_id>", methods=["POST"])
def delete_error_by_id(message_id):
    """
    This methods deletes a message in the list following its id
    :param message_id: the identifier of the message
    :return: ok message (this is not useful)
    """
    msg_manager = current_app.config['MSG_MANAGER']
    messages = msg_manager.messages

    index_msg = messages.index([msg for msg in messages if msg[0] == message_id][0])

    if 0 <= index_msg < len(messages):
        messages.pop(index_msg)

    return "OK"
