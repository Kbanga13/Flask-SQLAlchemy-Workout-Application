from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import validates
from sqlalchemy import CheckConstraint, UniqueConstraint
from datetime import date

db = SQLAlchemy()


class Exercise(db.Model):
    __tablename__ = 'exercises'

    __table_args__ = (
        CheckConstraint("length(name) > 0", name='exercise_name_not_empty'),
        CheckConstraint("length(category) > 0", name='exercise_category_not_empty'),
        UniqueConstraint('name', name='uq_exercise_name'),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    category = db.Column(db.String(50), nullable=False)
    equipment_needed = db.Column(db.Boolean, nullable=False, default=False)

    workout_exercises = db.relationship(
        'WorkoutExercise',
        back_populates='exercise',
        cascade='all, delete-orphan'
    )

    workouts = db.relationship(
        'Workout',
        secondary='workout_exercises',
        back_populates='exercises',
        viewonly=True
    )

    ALLOWED_CATEGORIES = {'cardio', 'strength', 'flexibility', 'balance', 'endurance'}

    @validates('name')
    def validate_name(self, key, value):
        if not value or not value.strip():
            raise ValueError("Exercise name cannot be empty")
        if len(value) > 80:
            raise ValueError("Exercise name must be 80 characters or fewer")
        return value.strip()

    @validates('category')
    def validate_category(self, key, value):
        if not value or not value.strip():
            raise ValueError("Category cannot be empty")
        if value.lower() not in self.ALLOWED_CATEGORIES:
            raise ValueError(
                f"Category must be one of: {', '.join(sorted(self.ALLOWED_CATEGORIES))}"
            )
        return value.lower()

    @validates('equipment_needed')
    def validate_equipment_needed(self, key, value):
        if not isinstance(value, bool):
            raise ValueError("equipment_needed must be a boolean")
        return value

    def __repr__(self):
        return f"<Exercise {self.id}: {self.name} ({self.category})>"


class Workout(db.Model):
    __tablename__ = 'workouts'

    __table_args__ = (
        CheckConstraint('duration_minutes > 0', name='workout_duration_positive'),
        CheckConstraint('duration_minutes <= 600', name='workout_duration_max'),
    )

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text)

    workout_exercises = db.relationship(
        'WorkoutExercise',
        back_populates='workout',
        cascade='all, delete-orphan'
    )

    exercises = db.relationship(
        'Exercise',
        secondary='workout_exercises',
        back_populates='workouts',
        viewonly=True
    )

    @validates('date')
    def validate_date(self, key, value):
        if value is None:
            raise ValueError("Workout date is required")
        if value > date.today():
            raise ValueError("Workout date cannot be in the future")
        return value

    @validates('duration_minutes')
    def validate_duration_minutes(self, key, value):
        if value is None:
            raise ValueError("Duration is required")
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError("Duration must be an integer")
        if value <= 0:
            raise ValueError("Duration must be positive")
        if value > 600:
            raise ValueError("Duration cannot exceed 600 minutes (10 hours)")
        return value

    @validates('notes')
    def validate_notes(self, key, value):
        if value is not None and len(value) > 1000:
            raise ValueError("Notes must be 1000 characters or fewer")
        return value

    def __repr__(self):
        return f"<Workout {self.id}: {self.date} ({self.duration_minutes} min)>"


class WorkoutExercise(db.Model):
    __tablename__ = 'workout_exercises'

    __table_args__ = (
        CheckConstraint('reps >= 0', name='we_reps_non_negative'),
        CheckConstraint('sets >= 0', name='we_sets_non_negative'),
        CheckConstraint('duration_seconds >= 0', name='we_duration_non_negative'),
        CheckConstraint(
            '(reps > 0 AND sets > 0) OR duration_seconds > 0',
            name='we_requires_reps_sets_or_duration'
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    workout_id = db.Column(
        db.Integer,
        db.ForeignKey('workouts.id', ondelete='CASCADE'),
        nullable=False
    )
    exercise_id = db.Column(
        db.Integer,
        db.ForeignKey('exercises.id', ondelete='CASCADE'),
        nullable=False
    )
    reps = db.Column(db.Integer, nullable=False, default=0)
    sets = db.Column(db.Integer, nullable=False, default=0)
    duration_seconds = db.Column(db.Integer, nullable=False, default=0)

    workout = db.relationship('Workout', back_populates='workout_exercises')
    exercise = db.relationship('Exercise', back_populates='workout_exercises')

    @validates('reps', 'sets', 'duration_seconds')
    def validate_non_negative(self, key, value):
        if value is None:
            return 0
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(f"{key} must be an integer")
        if value < 0:
            raise ValueError(f"{key} cannot be negative")
        return value

    def __repr__(self):
        return (
            f"<WorkoutExercise {self.id}: workout={self.workout_id} "
            f"exercise={self.exercise_id}>"
        )
