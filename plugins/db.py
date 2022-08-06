import psycopg2
from configs import DB_NAME, DB_USER, DB_HOST, DB_PASS


'''
users table:
+----------+-------------+------------+----------+----------+
|    id    |  fist_name  | last_name  | username |  is_bot  |
+----------+-------------+------------+----------+----------+
| int(pk)  |     str     |    str     |   str    |   bool   |
+----------+-------------+------------+----------+----------+
'''


class database(object):

    def __init__(self):
        self.con = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
        )
        # host=DB_HOST
        self.cur = self.con.cursor()

    def create_table(self):
        with self.con:
            self.cur.execute(
                'create table users'
                '(id bigint primary key not null,'
                'first_name           varchar(64),'
                'last_name            varchar(64),'
                'username             varchar(32),'
                'is_bot               bool not null)'
            )
            self.con.commit()

    def show_users(self) -> None:
        with self.con:
            self.cur.execute("select * from users")
            items = self.cur.fetchall()
            for i in items:
                print(i)
            return items

    def is_user_exist(self, user_info: dict) -> bool:
        with self.con:
            self.cur.execute(
                f"SELECT COUNT(1) FROM users WHERE id = {user_info.id};")
            res = self.cur.fetchall()
            for i in res:
                is_exist = i[0]

            # if exist
            if is_exist == 1:
                return True
            return False

    def remove_user(self, user_info: dict) -> None:
        pass

    def add_user(self, user_info: dict) -> None:
        with self.con:
            # TODO: choose better name for everything
            user = {
                'id': user_info.id,
                'first_name': user_info.first_name,
                'last_name': user_info.last_name,
                'username': user_info.username,
                'is_bot': user_info.is_bot
            }

            for k, v in user.items():
                if v is None:
                    user[k] = 'NULL'

            self.cur.execute(
                f"insert into users(id, first_name, last_name, username, is_bot)"
                f"values ({user['id']}, '{user['first_name']}',"
                f"'{user['last_name']}', '{user['username']}',"
                f"{user['is_bot']});"
            )
            self.con.commit()

