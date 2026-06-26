from flask import Flask, make_response, request
from flask_migrate import Migrate

from models import db, Exercise, Workout, WorkoutExercise

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
    workouts = Workout.query.all()
    return make_response(
        [{"id": w.id, "date": str(w.date), "duration_minutes": w.duration_minutes} for w in workouts],
        200,
    )


@app.route('/workouts/<int:id>', methods=['GET'])
def get_workout(id):
    workout = db.session.get(Workout, id)
    if workout is None:
        return make_response({"error": "Workout not found"}, 404)
    return make_response(
        {"id": workout.id, "date": str(workout.date), "duration_minutes": workout.duration_minutes},
        200,
    )


@app.route('/workouts', methods=['POST'])
def create_workout():
    return make_response({"message": "create_workout not implemented yet"}, 501)


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
    exercises = Exercise.query.all()
    return make_response(
        [{"id": e.id, "name": e.name, "category": e.category} for e in exercises],
        200,
    )


@app.route('/exercises/<int:id>', methods=['GET'])
def get_exercise(id):
    exercise = db.session.get(Exercise, id)
    if exercise is None:
        return make_response({"error": "Exercise not found"}, 404)
    return make_response(
        {"id": exercise.id, "name": exercise.name, "category": exercise.category,
         "equipment_needed": exercise.equipment_needed},
        200,
    )


@app.route('/exercises', methods=['POST'])
def create_exercise():
    return make_response({"message": "create_exercise not implemented yet"}, 501)


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
    return make_response({"message": "add_exercise_to_workout not implemented yet"}, 501)


if __name__ == '__main__':
    app.run(port=5555, debug=True)
