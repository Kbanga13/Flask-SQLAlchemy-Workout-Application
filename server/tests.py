"""Lightweight tests for models, schemas, and endpoints.

Run with:  python tests.py
Uses an in-memory SQLite DB so the real app.db is not touched.
"""
import json
import unittest
from datetime import date, timedelta

from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

import app as app_module
from models import db, Exercise, Workout, WorkoutExercise
from schemas import (
    exercise_schema, workout_schema, workout_exercise_schema,
)


class BaseCase(unittest.TestCase):
    def setUp(self):
        self.app = app_module.app
        self.app.config['TESTING'] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        # Wipe data between tests so the existing app.db is reusable.
        WorkoutExercise.query.delete()
        Workout.query.delete()
        Exercise.query.delete()
        db.session.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        WorkoutExercise.query.delete()
        Workout.query.delete()
        Exercise.query.delete()
        db.session.commit()
        db.session.remove()
        self.ctx.pop()


class TestModelValidations(BaseCase):
    def test_exercise_name_required(self):
        with self.assertRaises(ValueError):
            Exercise(name="", category="cardio", equipment_needed=False)

    def test_exercise_category_must_be_allowed(self):
        with self.assertRaises(ValueError):
            Exercise(name="X", category="dancing", equipment_needed=False)

    def test_workout_future_date_rejected(self):
        with self.assertRaises(ValueError):
            Workout(date=date.today() + timedelta(days=1), duration_minutes=30)

    def test_workout_duration_must_be_positive(self):
        with self.assertRaises(ValueError):
            Workout(date=date.today(), duration_minutes=0)

    def test_workout_duration_capped(self):
        with self.assertRaises(ValueError):
            Workout(date=date.today(), duration_minutes=601)


class TestTableConstraints(BaseCase):
    def test_unique_exercise_name(self):
        db.session.add(Exercise(name="A", category="cardio", equipment_needed=False))
        db.session.commit()
        db.session.add(Exercise(name="A", category="strength", equipment_needed=False))
        with self.assertRaises(IntegrityError):
            db.session.commit()
        db.session.rollback()

    def test_workout_exercise_requires_quantity(self):
        e = Exercise(name="A", category="cardio", equipment_needed=False)
        w = Workout(date=date.today(), duration_minutes=30)
        db.session.add_all([e, w])
        db.session.commit()
        db.session.add(WorkoutExercise(workout=w, exercise=e, reps=0, sets=0, duration_seconds=0))
        with self.assertRaises(IntegrityError):
            db.session.commit()
        db.session.rollback()

    def test_cascade_delete_workout(self):
        e = Exercise(name="A", category="cardio", equipment_needed=False)
        w = Workout(date=date.today(), duration_minutes=30)
        db.session.add_all([e, w])
        db.session.commit()
        db.session.add(WorkoutExercise(workout=w, exercise=e, duration_seconds=60))
        db.session.commit()
        self.assertEqual(WorkoutExercise.query.count(), 1)
        db.session.delete(w)
        db.session.commit()
        self.assertEqual(WorkoutExercise.query.count(), 0)


class TestSchemaValidations(BaseCase):
    def test_exercise_rejects_blank_name(self):
        with self.assertRaises(ValidationError):
            exercise_schema.load({"name": "   ", "category": "cardio"})

    def test_workout_rejects_future_date(self):
        with self.assertRaises(ValidationError):
            workout_schema.load({"date": "2999-01-01", "duration_minutes": 30})

    def test_workout_exercise_requires_quantity(self):
        with self.assertRaises(ValidationError):
            workout_exercise_schema.load({"reps": 0, "sets": 0, "duration_seconds": 0})

    def test_workout_exercise_accepts_duration_only(self):
        data = workout_exercise_schema.load({"duration_seconds": 60})
        self.assertEqual(data["duration_seconds"], 60)


class TestEndpoints(BaseCase):
    def _seed(self):
        e1 = Exercise(name="Push Up", category="strength", equipment_needed=False)
        e2 = Exercise(name="Running", category="cardio", equipment_needed=False)
        w = Workout(date=date.today(), duration_minutes=30, notes="test")
        db.session.add_all([e1, e2, w])
        db.session.commit()
        db.session.add(WorkoutExercise(workout=w, exercise=e1, reps=10, sets=3))
        db.session.commit()
        return e1, e2, w

    def test_get_workouts_includes_nested(self):
        e1, _, w = self._seed()
        resp = self.client.get('/workouts')
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertEqual(len(body), 1)
        self.assertEqual(body[0]['workout_exercises'][0]['exercise_name'], 'Push Up')

    def test_get_workout_404(self):
        resp = self.client.get('/workouts/999')
        self.assertEqual(resp.status_code, 404)

    def test_post_workout_valid(self):
        resp = self.client.post(
            '/workouts',
            data=json.dumps({"date": str(date.today()), "duration_minutes": 45}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 201)

    def test_post_workout_invalid_future(self):
        resp = self.client.post(
            '/workouts',
            data=json.dumps({"date": "2999-01-01", "duration_minutes": 45}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn('date', resp.get_json()['errors'])

    def test_post_exercise_duplicate_name(self):
        self._seed()
        resp = self.client.post(
            '/exercises',
            data=json.dumps({"name": "Push Up", "category": "strength"}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 400)

    def test_post_workout_exercise(self):
        _, e2, w = self._seed()
        resp = self.client.post(
            f'/workouts/{w.id}/exercises/{e2.id}/workout_exercises',
            data=json.dumps({"duration_seconds": 900}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 201)

    def test_post_workout_exercise_missing_parent(self):
        resp = self.client.post(
            '/workouts/999/exercises/1/workout_exercises',
            data=json.dumps({"duration_seconds": 60}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 404)

    def test_delete_workout_cascades(self):
        _, _, w = self._seed()
        self.assertEqual(WorkoutExercise.query.count(), 1)
        resp = self.client.delete(f'/workouts/{w.id}')
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(WorkoutExercise.query.count(), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
