import main as game_main


def test_create_game_session_initializes_expected_groups_and_player():
    session = game_main.create_game_session()

    assert session["player"] in session["updatable"]
    assert session["player"] in session["drawable"]
    assert session["health"] == session["max_health"]
    assert session["invuln_remaining"] == 0.0

    # Lightweight integration smoke-check: one update tick should not crash.
    session["updatable"].update(0.016)

    for group_key in ("updatable", "drawable", "asteroids", "shots", "explosions"):
        session[group_key].empty()

