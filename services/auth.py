from flask import session


def usuario_logado():
    return session.get("logado") is True


def usuario_admin():
    return session.get("tipo") == "admin"
