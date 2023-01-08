import pytest

from missing_persons_match_unidentified_dead_bodies.users.models import User
from missing_persons_match_unidentified_dead_bodies.users.tests.factories import (
    UserFactory,
)


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def user(db) -> User:
    return UserFactory()
