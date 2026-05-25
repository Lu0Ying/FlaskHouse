from app import create_app, db
from app.models import User, House, LeaseContract

app = create_app()


@app.shell_context_processor
def make_shell_context():
    """为 flask shell 提供上下文"""
    return {'db': db, 'User': User, 'House': House, 'LeaseContract': LeaseContract}


if __name__ == '__main__':
    app.run(debug=True)
