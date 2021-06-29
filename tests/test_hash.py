import io

from chord.hash import hash_value, main


def test_hash():
    assert hash_value("Hello, world!") == 108
    assert hash_value("FOO BAR 1234566789") == 129
    assert hash_value("Portland, OR") == 175
    assert hash_value("555-123-4567") == 202


def test_hash_cli():
    cmd = ["Hello, world!"]
    expected = "Value \"Hello, world!\" has digest \"108\""
    actual = io.StringIO()

    main(actual, cmd)
    assert actual.getvalue().strip() == expected
