from flask import Flask, make_response, request
from flask_migrate import Migrate
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from models import db, Exercise, Workout, WorkoutExercise
from schemas import (
    exercise_schema, exercises_schema,
    workout_schema, workouts_schema,
    workout_exercise_schema,
)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

migrate = Migrate(app, db)
db.init_app(app)


@app.route('/')
def index():
    return make_response({"message": "Workout API"}, 200)


# ----- Workouts -----

@app.route('/workouts', methods=['GET'])
def list_workouts():
    return make_response(workouts_schema.dump(Workout.query.all()), 200)


@app.route('/workouts/<int:id>', methods=['GET'])
def get_workout(id):
    workout = db.session.get(Workout, id)
    if workout is None:
        return make_response({"error": "Workout not found"}, 404)
    return make_response(workout_schema.dump(workout), 200)


@app.route('/workouts', methods=['POST'])
def create_workout():
    try:
        data = workout_schema.load(request.get_json() or {})
    except ValidationError as err:
        return make_response({"errors": err.messages}, 400)

    try:
        workout = Workout(**data)
        db.session.add(workout)
        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        return make_response({"errors": [str(e)]}, 400)
    except IntegrityError as e:
        db.session.rollback()
        return make_response({"errors": [str(e.orig)]}, 400)

    return make_response(workout_schema.dump(workout), 201)


@app.route('/workouts/<int:id>', methods=['DELETE'])
def delete_workout(id):
    workout = db.session.get(Workout, id)
    if workout is None:
        return make_response({"error": "Workout not found"}, 404)
    db.session.delete(workout)
    db.session.commit()
    return make_response({}, 204)


# ----- Exercises -----

@app.route('/exercises', methods=['GET'])
def list_exercises():
    return make_response(exercises_schema.dump(Exercise.query.all()), 200)


@app.route('/exercises/<int:id>', methods=['GET'])
def get_exercise(id):
    exercise = db.session.get(Exercise, id)
    if exercise is None:
        return make_response({"error": "Exercise not found"}, 404)
    return make_response(exercise_schema.dump(exercise), 200)


@app.route('/exercises', methods=['POST'])
def create_exercise():
    try:
        data = exercise_schema.load(request.get_json() or {})
    except ValidationError as err:
        return make_response({"errors": err.messages}, 400)

    try:
        exercise = Exercise(**data)
        db.session.add(exercise)
        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        return make_response({"errors": [str(e)]}, 400)
    except IntegrityError as e:
        db.session.rollback()
        return make_response({"errors": [str(e.orig)]}, 400)

    return make_response(exercise_schema.dump(exercise), 201)


@app.route('/exercises/<int:id>', methods=['DELETE'])
def delete_exercise(id):
    exercise = db.session.get(Exercise, id)
    if exercise is None:
        return make_response({"error": "Exercise not found"}, 404)
    db.session.delete(exercise)
    db.session.commit()
    return make_response({}, 204)


# ----- WorkoutExercises (join) -----

@app.route('/workouts/<int:workout_id>/exercises/<int:exercise_id>/workout_exercises',
           methods=['POST'])
def add_exercise_to_workout(workout_id, exercise_id):
    workout = db.session.get(Workout, workout_id)
    if workout is None:
        return make_response({"error": "Workout not found"}, 404)
    exercise = db.session.get(Exercise, exercise_id)
    if exercise is None:
        return make_response({"error": "Exercise not found"}, 404)

    try:
        data = workout_exercise_schema.load(request.get_json() or {})
    except ValidationError as err:
        return make_response({"errors": err.messages}, 400)

    try:
        we = WorkoutExercise(workout=workout, exercise=exercise, **data)
        db.session.add(we)
        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        return make_response({"errors": [str(e)]}, 400)
    except IntegrityError as e:
        db.session.rollback()
        return make_response({"errors": [str(e.orig)]}, 400)

    return make_response(workout_exercise_schema.dump(we), 201)


if __name__ == '__main__':
    app.run(port=5555, debug=True)
