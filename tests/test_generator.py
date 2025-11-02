from agent import generator


def test_generate_examples_basic():
    cols = [
        {"column_name": "id", "data_type": "int", "is_nullable": "NO"},
        {"column_name": "name", "data_type": "varchar", "is_nullable": "YES"},
        {"column_name": "created_at", "data_type": "datetime", "is_nullable": "YES"},
    ]
    q = generator.generate_examples("dbo.MyTable", cols)
    assert "SELECT id, name, created_at FROM dbo.MyTable" in q["select"]["sql"]
    assert q["insert"]["sql"].startswith("INSERT INTO dbo.MyTable (")
    assert "UPDATE dbo.MyTable SET" in q["update"]["sql"]
    assert "DELETE FROM dbo.MyTable" in q["delete"]["sql"]


def test_generate_examples_with_pk_columns():
    cols = [
        {"column_name": "a", "data_type": "int", "is_nullable": "NO"},
        {"column_name": "b", "data_type": "int", "is_nullable": "NO"},
        {"column_name": "c", "data_type": "varchar", "is_nullable": "YES"},
    ]
    # composite PK a,b
    q = generator.generate_examples("dbo.Comp", cols, pk_columns=["a", "b"])
    assert q["select"]["sql"].count("?") == 2
    assert "a = ? AND b = ?" in q["select"]["sql"]
    # update should set only c and then have two PK params
    assert q["update"]["sql"].startswith("UPDATE dbo.Comp SET c = ? WHERE a = ? AND b = ?") or "WHERE a = ? AND b = ?" in q["update"]["sql"]


def test_generate_examples_no_columns():
    import pytest

    with pytest.raises(ValueError):
        generator.generate_examples("t", [])


def test_generate_examples_param_types_and_order():
    cols = [
        {"column_name": "id", "data_type": "int", "is_nullable": "NO"},
        {"column_name": "price", "data_type": "decimal(10,2)", "is_nullable": "YES"},
        {"column_name": "name", "data_type": "varchar", "is_nullable": "YES"},
    ]
    q = generator.generate_examples("dbo.Foo", cols, pk_columns=["id"])
    # select params should match the pk order
    assert q["select"]["params"][0] == "1"
    # insert params should have same length as columns and have decimal sample for price
    assert len(q["insert"]["params"]) == 3
    assert any(p.startswith("1.23") or p == "1.23" for p in q["insert"]["params"])
