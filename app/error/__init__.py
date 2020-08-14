from flask import Blueprint

error = Blueprint('error', __name__)

from app.error import handlers