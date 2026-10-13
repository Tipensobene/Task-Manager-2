from getpass import getpass

import psycopg
from psycopg.rows import dict_row

password = getpass(prompt='Enter your password: \n')


#输入放在连接建立前防止等待消耗资源
task_id = int(input('Enter task id: \n'))

try:
    with psycopg.connect(
            host='localhost',
            port=5432,
            dbname="task_manager_learning",
            user='postgres',
            password=password
    ) as connection:

        with connection.cursor(row_factory=dict_row) as cursor:

            cursor.execute(
                '''
                select
                    t.id,
                    t.title,
                    t.done,
                    t.priority,
                    coalesce(
                        array_agg(tg.name order by tg.name)
                            filter(where tg.name is not null),
                        array[]::text[]
                    )as tags
                from tasks as t
                left join task_tags as tt
                    on t.id = tt.task_id
                left join tags as tg
                    on tg.id = tt.tag_id
                where t.id=%s
                group by t.id, t.title,t.done,t.priority;
                ''',
                (task_id,)
            )

            row = cursor.fetchone()
            if row is None:
                print('Task not found')
            else:
                print(row)
                print()
                print(row['title'])

            # rows = cursor.fetchall()

            # for row in rows:
            #     print(row)

except psycopg.OperationalError as error:
    print("数据库连接失败")
    print(type(error).__name__)

except psycopg.errors.SyntaxError as error:
    print("SQL语法错误")
    print(type(error).__name__)