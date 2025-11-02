from agent import db_client


def test_parse_connection_string_basic():
    s = "Driver={ODBC Driver 18 for SQL Server};Server=localhost,1433;Database=Chinook;Uid=sa;Pwd=pass;"
    parsed = db_client.parse_connection_string(s)
    assert parsed.get('driver') == '{ODBC Driver 18 for SQL Server}'
    assert parsed.get('server') == 'localhost,1433'
    assert parsed.get('database') == 'Chinook'
    assert parsed.get('uid') == 'sa'


def test_parse_connection_string_empty_values():
    s = "Driver={X};Server=;Database=;"
    parsed = db_client.parse_connection_string(s)
    assert parsed.get('driver') == '{X}'
    # empty server/database should be present but empty
    assert 'server' in parsed
    assert parsed.get('server') == ''
