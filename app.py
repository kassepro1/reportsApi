from init_conf import create_app


app = create_app()

if __name__ == '__main__':
    app.run(host=app.config['QR_HOST'], port=app.config['QR_PORT'])

