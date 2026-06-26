from datetime import date

from marshmallow import Schema, fields, validate, validates, validates_schema, ValidationError

from models import Exercise


ALLOWED_CATEGORIES = sorted(Exercise.ALLOWED_CATEGORIES)


class ExerciseSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=80, error="Name must be 1-80 characters"),
    )
    category = fields.Str(
        required=True,
        validate=validate.OneOf(
            ALLOWED_CATEGORIES,
            error=f"Category must be one of: {', '.join(ALLOWED_CATEGORIES)}",
        ),
    )
    equipment_needed = fields.Bool(load_default=False)

    @validates('name')
    def strip_name(self, value, **kwargs):
        if not value.strip():
            raise ValidationError("Name cannot be blank or whitespace")


class WorkoutExerciseNestedSchema(Schema):
    """Nested representation of a WorkoutExercise inside a Workout response."""
    id = fields.Int(dump_only=True)
    exercise_id = fields.Int(dump_only=True)
    exercise_name = fields.Method('get_exercise_name', dump_only=True)
    reps = fields.Int()
    sets = fields.Int()
    duration_seconds = fields.Int()

    def get_exercise_name(self, obj):
        return obj.exercise.name if obj.exercise else None


class WorkoutSchema(Schema):
    id = fields.Int(dump_only=True)
    date = fields.Date(required=True)
    duration_minutes = fields.Int(
        required=True,
        validate=validate.Range(
            min=1, max=600,
            error="duration_minutes must be between 1 and 600",
        ),
    )
    notes = fields.Str(
        load_default=None,
        allow_none=True,
        validate=validate.Length(max=1000, error="Notes must be 1000 characters or fewer"),
    )
    workout_exercises = fields.List(
        fields.Nested(WorkoutExerciseNestedSchema), dump_only=True
    )

    @validates('date')
    def not_future(self, value, **kwargs):
        if value > date.today():
            raise ValidationError("Workout date cannot be in the future")


class WorkoutExerciseSchema(Schema):
    id = fields.Int(dump_only=True)
    workout_id = fields.Int(dump_only=True)
    exercise_id = fields.Int(dump_only=True)
    reps = fields.Int(
        load_default=0,
        validate=validate.Range(min=0, error="reps cannot be negative"),
    )
    sets = fields.Int(
        load_default=0,
        validate=validate.Range(min=0, error="sets cannot be negative"),
    )
    duration_seconds = fields.Int(
        load_default=0,
        validate=validate.Range(min=0, error="duration_seconds cannot be negative"),
    )

    @validates_schema
    def require_quantity(self, data, **kwargs):
        reps = data.get('reps', 0) or 0
        sets = data.get('sets', 0) or 0
        duration = data.get('duration_seconds', 0) or 0
        if not ((reps > 0 and sets > 0) or duration > 0):
            raise ValidationError(
                "Must provide either (reps > 0 AND sets > 0) or duration_seconds > 0",
                field_name='_schema',
            )


exercise_schema = ExerciseSchema()
exercises_schema = ExerciseSchema(many=True)
workout_schema = WorkoutSchema()
workouts_schema = WorkoutSchema(many=True)
workout_exercise_schema = WorkoutExerciseSchema()
