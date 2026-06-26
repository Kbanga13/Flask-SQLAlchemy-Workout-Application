#!/usr/bin/env python3
from datetime import date, timedelta

from app import app
from models import db, Exercise, Workout, WorkoutExercise


def run():
    with app.app_context():
        print("Clearing existing data...")
        WorkoutExercise.query.delete()
        Workout.query.delete()
        Exercise.query.delete()
        db.session.commit()

        print("Seeding exercises...")
        pushup = Exercise(name="Push Up", category="strength", equipment_needed=False)
        squat = Exercise(name="Squat", category="strength", equipment_needed=False)
        running = Exercise(name="Running", category="cardio", equipment_needed=False)
        plank = Exercise(name="Plank", category="endurance", equipment_needed=False)
        yoga = Exercise(name="Yoga Flow", category="flexibility", equipment_needed=True)
        db.session.add_all([pushup, squat, running, plank, yoga])
        db.session.commit()

        print("Seeding workouts...")
        today = date.today()
        w1 = Workout(date=today - timedelta(days=2), duration_minutes=45, notes="Full body strength")
        w2 = Workout(date=today - timedelta(days=1), duration_minutes=30, notes="Quick cardio session")
        w3 = Workout(date=today, duration_minutes=60, notes="Flexibility and core")
        db.session.add_all([w1, w2, w3])
        db.session.commit()

        print("Linking workouts and exercises...")
        db.session.add_all([
            WorkoutExercise(workout=w1, exercise=pushup, reps=15, sets=3, duration_seconds=0),
            WorkoutExercise(workout=w1, exercise=squat, reps=20, sets=3, duration_seconds=0),
            WorkoutExercise(workout=w2, exercise=running, reps=0, sets=0, duration_seconds=1800),
            WorkoutExercise(workout=w3, exercise=plank, reps=0, sets=3, duration_seconds=60),
            WorkoutExercise(workout=w3, exercise=yoga, reps=0, sets=0, duration_seconds=1200),
        ])
        db.session.commit()

        print("Done.")


if __name__ == '__main__':
    run()
