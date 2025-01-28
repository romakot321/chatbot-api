from app.db.tables import User
from sqladmin import ModelView


class UserView(ModelView, model=User):
    column_list = "__all__"
    column_searchable_list = [User.id]
    column_default_sort = [(User.id, True)]

