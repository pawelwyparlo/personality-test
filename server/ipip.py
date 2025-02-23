from flask import Blueprint
from .questions import QUESTIONS

bp = Blueprint('ipip', __name__, url_prefix='/ipip')


@bp.route('/questions')
def get_questions():
    return QUESTIONS

@bp.route('/results')
def get_results():
    return 
