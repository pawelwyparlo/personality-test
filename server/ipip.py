from flask import Blueprint

bp = Blueprint('ipip', __name__, url_prefix='/ipip')


@bp.route('/questions')
def get_questions():
    return '<p>Results</p>'

@bp.route('/results')
def get_results():
    return 
