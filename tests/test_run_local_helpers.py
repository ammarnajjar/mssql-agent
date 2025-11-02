from agent.utils import sqlalchemy_to_odbc


def test_sqlalchemy_to_odbc_basic():
    url = 'mssql+pyodbc://sa:pw@localhost:1433/Chinook?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes'
    out = sqlalchemy_to_odbc(url)
    assert 'Driver={' in out and 'Server=localhost,1433' in out and 'Database=Chinook' in out

