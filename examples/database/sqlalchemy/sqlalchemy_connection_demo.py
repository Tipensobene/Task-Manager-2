from getpass import getpass


from sqlalchemy import create_engine,URL,text

password=getpass("Enter your password:\n")

database_url=URL.create(
    drivername='postgresql+psycopg',
    username="postgres",
    password=password,
    host="localhost",
    port=5432,
    database="task_manager_learning"
)

engine = create_engine(database_url)

with engine.connect() as connection:
    result=connection.execute(
        text("select current_database();")
    )

    row=result.fetchone()

    if row is not None:
        print(row[0])