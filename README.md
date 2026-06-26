# Flask-SQLAlchemy Workout Application

A RESTful Flask API for tracking workouts and the exercises performed in them. Built with Flask, SQLAlchemy, Flask-Migrate, and Marshmallow.

## Description

This API manages three resources:

- **Exercises** — individual movements (Push Up, Running, etc.) with a category and an equipment flag.
- **Workouts** — a session on a given date, with a duration and optional notes.
- **WorkoutExercises** — the join between a workout and an exercise, recording reps, sets, and/or duration.

Relationships:

- A `Workout` has many `Exercises` through `WorkoutExercises`.
- An `Exercise` has many `Workouts` through `WorkoutExercises`.
- Deleting a `Workout` or `Exercise` cascades and removes the related `WorkoutExercise` rows.

Validation is enforced at three layers — table constraints (CHECK / UNIQUE / NOT NULL), SQLAlchemy `@validates` methods, and Marshmallow schemas.

## Installation

Requires Python 3.10+.

Using `pipenv`:

```bash
pipenv install
pipenv shell
```

Or with `pip`:

```bash
pip install -r requirements.txt
```

### Database setup

From the `server/` directory:

```bash
cd server

# Run migrations to create the SQLite database
FLASK_APP=app.py flask db upgrade head

# Populate with sample data
python seed.py
```

> If `migrations/` does not already exist, run `flask db init` first, then `flask db migrate -m "init"` before `flask db upgrade head`.

The database file is created at `server/instance/app.db`.

## Running the app

From the `server/` directory:

```bash
FLASK_APP=app.py flask run --port 5555
```

Or directly:

```bash
python app.py
```

The API will be available at `http://127.0.0.1:5555`.

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/workouts` | List all workouts, with nested workout_exercises (reps/sets/duration + exercise name). |
| GET | `/workouts/<id>` | Fetch one workout by id, including its workout_exercises. Returns 404 if not found. |
| POST | `/workouts` | Create a workout. Body: `{date, duration_minutes, notes?}`. Returns 201 + the workout, or 400 on validation error. |
| DELETE | `/workouts/<id>` | Delete a workout. Cascades to its workout_exercises. Returns 204, or 404 if not found. |
| GET | `/exercises` | List all exercises. |
| GET | `/exercises/<id>` | Fetch one exercise by id. Returns 404 if not found. |
| POST | `/exercises` | Create an exercise. Body: `{name, category, equipment_needed?}`. Returns 201, or 400 (e.g. duplicate name, invalid category). |
| DELETE | `/exercises/<id>` | Delete an exercise. Cascades to its workout_exercises. Returns 204, or 404. |
| POST | `/workouts/<workout_id>/exercises/<exercise_id>/workout_exercises` | Add an exercise to a workout. Body: `{reps?, sets?, duration_seconds?}`. Must supply either reps+sets or duration. Returns 201, 400, or 404 if either parent is missing. |

### Request / response examples

Create a workout:

```bash
curl -X POST http://127.0.0.1:5555/workouts \
  -H "Content-Type: application/json" \
  -d '{"date": "2026-06-20", "duration_minutes": 45, "notes": "Leg day"}'
```

Response:

```json
{
  "id": 4,
  "date": "2026-06-20",
  "duration_minutes": 45,
  "notes": "Leg day",
  "workout_exercises": []
}
```

Add an exercise to that workout:

```bash
curl -X POST http://127.0.0.1:5555/workouts/4/exercises/2/workout_exercises \
  -H "Content-Type: application/json" \
  -d '{"reps": 12, "sets": 4}'
```

Validation error example (future date):

```json
{ "errors": { "date": ["Workout date cannot be in the future"] } }
```

## Validations

### Table constraints

- `exercises.name` — NOT NULL, UNIQUE, length > 0
- `exercises.category` — NOT NULL, length > 0
- `workouts.duration_minutes` — between 1 and 600
- `workout_exercises.reps` / `sets` / `duration_seconds` — non-negative
- `workout_exercises` — must have either (reps > 0 AND sets > 0) OR duration_seconds > 0
- FKs cascade on delete

### Model validations (`@validates`)

- `Exercise.name` — non-empty, trimmed, ≤80 chars
- `Exercise.category` — must be one of: cardio, strength, flexibility, balance, endurance
- `Workout.date` — required, cannot be in the future
- `Workout.duration_minutes` — required int, 1–600
- `Workout.notes` — ≤1000 chars
- `WorkoutExercise.reps` / `sets` / `duration_seconds` — non-negative integers

### Schema validations (Marshmallow)

- `name` — required, 1–80 chars, no whitespace-only
- `category` — must be one of the allowed values
- `date` — must not be in the future
- `duration_minutes` — required, range 1–600
- `notes` — ≤1000 chars
- `reps` / `sets` / `duration_seconds` — non-negative
- Cross-field rule: a `WorkoutExercise` must have either reps>0 AND sets>0, or duration_seconds>0

## Project structure

```
.
├── Pipfile
├── README.md
├── requirements.txt
└── server/
    ├── app.py            # Flask app + routes
    ├── models.py         # SQLAlchemy models, table constraints, model validations
    ├── schemas.py        # Marshmallow schemas + schema validations
    ├── seed.py           # Reset and reseed the database
    ├── migrations/       # Alembic migrations
    └── instance/
        └── app.db        # SQLite database (gitignored)
```
