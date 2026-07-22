"""Tests for the explicit development seed command."""

from app.models.users import User


def test_seed_command_is_safe_and_idempotent(app):
    runner = app.test_cli_runner()

    first_result = runner.invoke(args=["seed-db"])
    second_result = runner.invoke(args=["seed-db"])

    assert first_result.exit_code == 0
    assert second_result.exit_code == 0
    expected_message = (
        "No users were seeded because password hashing is not yet implemented."
    )
    assert expected_message in first_result.output
    assert expected_message in second_result.output

    with app.app_context():
        assert User.query.count() == 0
