from getpass import getpass

import psycopg


password = getpass("Enter your password:\n")
new_tag = "transaction-test"

try:
    with psycopg.connect(
        host="localhost",
        port=5432,
        dbname="task_manager_learning",
        user="postgres",
        password=password,
    ) as connection:
        with connection.cursor() as cursor:
            # TODO：使用参数化查询，将 new_tag 插入 tags 表。
            cursor.execute(
                '''
                insert into tags (name)
                values (%s);
                ''',
                (new_tag, )
            )
            print("第一条 INSERT 已执行")

            # TODO：使用参数化查询，再次插入已经存在的标签 python。
            cursor.execute(
                """
                insert into tags (name)
                values (%s);
                """,
                ('python',)
            )

except psycopg.errors.UniqueViolation:
    print("第二条 INSERT 失败，事务已回滚")
