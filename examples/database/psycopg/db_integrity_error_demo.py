from getpass import getpass

import psycopg


password = getpass("Enter your password:\n")

try:
    with psycopg.connect(
        host="localhost",
        port=5432,
        dbname="task_manager_learning",
        user="postgres",
        password=password,
    ) as connection:

        new_tag='python'
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                insert into tags (name)
                values (%s)
                ''',
                (new_tag,)
            )

except psycopg.errors.UniqueViolation as error:
    print("标签名称不能重复")
    print(type(error).__name__)