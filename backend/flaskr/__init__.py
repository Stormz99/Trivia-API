import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random
import sys
from settings import DB_NAME, DB_USER, DB_PASS, DB_HOST


from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    formatted_question = questions[start:end]
    return formatted_question


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app)
    """
    After_request decorator to set Access-Control-Allow
    """
    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        return response
    """
    Endpoint to handle GET requests
    for all available categories.
    """
    @app.route('/categories')
    def get_categories():
        try:

            categories = Category.query.order_by(Category.id).all()
            formatted_categories = [categorie.format()
                                    for categorie in categories]

            return jsonify({
                'success': True,
                'categories': {category.id: category.type for category in categories},
                'total_categories': len(formatted_categories)
            })
        except:
            abort(404)

    """
    @TODO:
    This endpoint  handles GET requests for questions,
    including pagination (every 10 questions).
    This endpoint returns a list of questions,
    number of total questions, current category, categories.
    """
    @app.route('/questions')
    def get_questions():
        questions = Question.query.all()

        categories = Category.query.order_by(Category.type).all()
        current_question = paginate_questions(request, questions)
        if len(current_question) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions': current_question,
            'total_questions': len(questions),
            'current_category': None,
            'categories': {category.id: category.type for category in categories},

        })

    """"
  Endpoint to DELETE question using a question ID.
    """

    @app.route("/questions/<int:question_id>", methods=["DELETE"])
    def delete_question(question_id):
        try:
            question = Question.query.filter(
                Question.id == question_id).one_or_none()
            question.delete()
            selection = Question.query.order_by(Question.id).all()
            current_question = paginate_questions(request, selection)

            return jsonify({
                'success': True,
                'deleted': question_id,
                'total_questions': len(Question.query.all())
            })
        except BaseException:
            abort(404)

    """"
    Endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.
    """

    @app.route('/questions', methods=['POST'])
    def add_question():
        body = request.get_json()
        new_question = body.get("question", ' ')
        new_answer_text = body.get("answer", ' ')
        new_category = body.get("category", ' ')
        new_difficulty_score = body.get("difficulty", ' ')
        try:
            if ((new_question == ' ') or (new_answer_text == ' ')
                    or (new_difficulty_score == ' ') or (new_category == ' ')):
                abort(422)
            else:
                question = Question(
                    question=new_question,
                    answer=new_answer_text,
                    category=new_category,
                    difficulty=new_difficulty_score)

                question.insert()
                selection = Question.query.order_by(Question.id).all()
                current_question = paginate_questions(request, selection)

                return jsonify({
                    "success": True,
                    "created": question.id,
                    "total_questions": len(Question.query.all())
                })
        except BaseException:
            abort(422)
    """
   Endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.
    """
    @app.route('/questions/search', methods=['POST'])
    def search_question():
        body = request.get_json()
        search_term=body['searchTerm']
        try:
                questions = Question.query.order_by(Question.id).filter(
                    Question.question.ilike("%" + search_term + "%")).all()

                current_questions = paginate_questions(request, questions)

                return jsonify({
                    'success': True,
                    'questions': current_questions
                })
                
        except:
            abort(422)
            

            
    
   

    """
      GET endpoint to get questions based on category.
    """
    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def get_questions_by_category_id(category_id):
        categories = Category.query.get(category_id)
        try:
            questions = Question.query.filter_by(
                category=str(category_id)).all()

            current_questions = paginate_questions(request, questions)

            return jsonify({
                'success': True,
                'questions': current_questions,
                'current_category': categories.type,
                'total_questions': len(questions)

            })
        except BaseException:
            abort(400)

    """
      POST endpoint to get questions to play the quiz.
    """
    @app.route('/quizzes', methods=['POST'])
    def play():
        previous_questions = request.get_json()['previous_questions']
        quiz_category = request.get_json()['quiz_category']
        print(quiz_category)

        query = Question.query.all()
        current_question = []

        if previous_questions is None:
            abort(422)
        else:
            for question in query:
                if len(previous_questions) == 0 and int(quiz_category['id']) != question.category:
                    current_question.append(question.format())
                else:
                    for previous in previous_questions:
                        if previous != question.id and int(quiz_category['id']) != question.category:
                            current_question.append(question.format())
        return jsonify({'question': random.choice(current_question), 'success': True})
       



    """
     Error handlers for all expected errors
    including 404 , 422 , 400 , 405 and 500
    """
    @app.errorhandler(404)
    def page_not_found(error):
        return jsonify({
            'success': False,
            'error': 404,
            'message': 'Resource Not Found'
        }), 404

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "Bad Request"}), 400

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "Unprocessable"}), 422

    @app.errorhandler(405)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 405,
            "message": "Method Not Allowed"}), 405

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "Internal Server Error"}), 500
    return app
