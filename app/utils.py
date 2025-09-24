from flask import request
from flask_login import current_user
from manage import db
from models import Log

def register_log(action, status="ok"):
    user_id = current_user.id if current_user.is_authenticated else None
    ip_address = request.remote_addr
    # adicionar company info opcionalmente
    log = Log(
        user_id=user_id,
        action=action,
        ip_address=ip_address,
        status=status
    )
    db.session.add(log)
    db.session.commit()
