import time


class Todos:
    class Todo:
        def __init__(self, free_id: int, title: str, content: str, due_date: int, status: str = 'PENDING'):
            self._id = free_id
            self._title = title
            self._content = content
            self._due_date = due_date
            self._status = status

        def get_todo_as_dict(self):
            return {"id": self._id, "title": self._title, "content": self._content, "status": self._status, "dueDate": self._due_date}

    def __init__(self):
        self._todo_dict = {}
        self._avail_id = 1
        self._titles = set()
        self._pending_todo_ids = set()
        self._late_todo_ids = set()
        self._done_todo_ids = set()

    def append(self, title: str, content: str, due_date: int, status: str = 'PENDING'):
        outcome = str()
        is_todo_valid = True

        if title in self._titles:
            is_todo_valid = False
            outcome = "title already exists"

        if is_todo_valid:
            current_timestamp_millis = int(round(time.time() * 1000))
            if due_date > current_timestamp_millis:
                self._todo_dict[self._avail_id] = Todos.Todo(self._avail_id, title, content, due_date, status)
                self._titles.add(title)
                if status == 'PENDING':
                    self._pending_todo_ids.add(self._avail_id)
                elif status == 'LATE':
                    self._late_todo_ids.add(self._avail_id)
                else:
                    self._done_todo_ids.add(self._avail_id)
                outcome = self._avail_id
                self._avail_id += 1
            else:
                outcome = "due date is in the past"
        return outcome

    def update(self, query_id, query_status):
        outcome = str()
        if query_id in self._todo_dict.keys():
            outcome = self._todo_dict[query_id]._status
            if outcome == 'PENDING':
                self._pending_todo_ids.remove(query_id)
            elif outcome == 'LATE':
                self._late_todo_ids.remove(query_id)
            else:
                self._done_todo_ids.remove(query_id)

            self._todo_dict[query_id]._status = query_status
            if query_status == 'PENDING':
                self._pending_todo_ids.add(query_id)
            elif query_status == 'LATE':
                self._late_todo_ids.add(query_id)
            else:
                self._done_todo_ids.add(query_id)
        else:
            outcome = 'no such TODO'
        return outcome

    def delete(self, query_id):
        outcome = str()
        if query_id in self._todo_dict.keys():
            self._titles.remove(self._todo_dict[query_id]._title)
            if self._todo_dict[query_id]._status == 'PENDING':
                self._pending_todo_ids.remove(query_id)
            elif self._todo_dict[query_id]._status == 'LATE':
                self._late_todo_ids.remove(query_id)
            else:
                self._done_todo_ids.remove(query_id)
            self._todo_dict.pop(query_id)
            outcome = len(self._todo_dict)
        else:
            outcome = 'no such TODO'
        return outcome

    def count_by_status(self, status: str = 'PENDING'):
        count = int()
        if status == 'ALL':
            count = len(self._todo_dict)
        elif status == 'PENDING':
            count = len(self._pending_todo_ids)
        elif status == 'LATE':
            count = len(self._late_todo_ids)
        elif status == 'DONE':
            count = len(self._done_todo_ids)
        else:
            count = -1
        return count

    def sort_todos_by_sort_by(self, criteria):
        sorted_list = list()
        if criteria == 'ID':
            sorted_list = sorted(self._todo_dict.values(), key=lambda todo: todo._id)
        elif criteria == 'DUE_DATE':
            sorted_list = sorted(self._todo_dict.values(), key=lambda todo: todo._due_date)
        elif criteria == 'TITLE':
            sorted_list = sorted(self._todo_dict.values(), key=lambda todo: todo._title)
        return sorted_list

    def filter_todos(self, status):
        filtered_todos = Todos()
        max_id = -1

        for key, value in self._todo_dict.items():
            if value._status == status:
                filtered_todos._todo_dict[key] = value
                filtered_todos._titles.add(value._title)
                if max_id < key:
                    max_id = key
                if status == 'PENDING':
                    filtered_todos._pending_todo_ids.add(key)
                elif status == 'LATE':
                    filtered_todos._late_todo_ids.add(key)
                elif status == 'DONE':
                    filtered_todos._done_todo_ids.add(key)
        filtered_todos.__avail_id = max_id + 1
        return filtered_todos
