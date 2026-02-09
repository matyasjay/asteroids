from game.config.constants import SCREEN_WIDTH, SCREEN_HEIGHT
from game.core.circleshape import CircleShape


def test_collides_with_uses_radius_distance():
    a = CircleShape(100, 100, 20)
    b = CircleShape(130, 100, 12)
    c = CircleShape(160, 100, 12)

    assert a.collides_with(b)
    assert not a.collides_with(c)


def test_wrap_around_screen_applies_all_edges():
    s = CircleShape(0, 0, 10)

    s.position.x = -11
    s.wrap_around_screen()
    assert s.position.x == SCREEN_WIDTH + s.radius

    s.position.x = SCREEN_WIDTH + s.radius + 1
    s.wrap_around_screen()
    assert s.position.x == -s.radius

    s.position.y = -11
    s.wrap_around_screen()
    assert s.position.y == SCREEN_HEIGHT + s.radius

    s.position.y = SCREEN_HEIGHT + s.radius + 1
    s.wrap_around_screen()
    assert s.position.y == -s.radius

