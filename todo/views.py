import loguru
from django.http import HttpResponse
from . import utils
import json
from loguru import logger
import time
from sys import stdout


todos = utils.Todos()

global_request_counter = 1

request_logger_level = "INFO"
todo_logger_level = "INFO"
request_logger_id = list()
todo_logger_id = int()


def make_filter(name):
    def filter_record(record):
        return record["extra"].get("name") == name
    return filter_record


request_logger_id.append(logger.add(stdout, level=request_logger_level, format="{time:DD-MM-YYYY HH:mm:ss.SSS} {level}: {message}", filter=make_filter("request_logger")))
request_logger_id.append(logger.add("logs/requests.log", level=request_logger_level, format="{time:DD-MM-YYYY HH:mm:ss.SSS} {level}: {message}", filter=make_filter("request_logger")))
todo_logger_id = logger.add("logs/todos.log", level=todo_logger_level, format="{time:DD-MM-YYYY HH:mm:ss.SSS} {level}: {message}", filter=make_filter("todo_logger"))

request_logger = logger.bind(name="request_logger")
todo_logger = logger.bind(name="todo_logger")


def log_request(resource_name, http_verb):
    global global_request_counter
    request_logger.info(
        f"Incoming request | #{global_request_counter} | resource: {resource_name} | HTTP Verb: {http_verb}  | request #{global_request_counter}")


def log_request_duration(func):
    def wrapper(*args, **kwargs):
        global global_request_counter
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_ms = (end_time - start_time) * 1000
        request_logger.debug(f"Request #{global_request_counter} duration: {elapsed_ms:.3f}ms | request #{global_request_counter}")
        global_request_counter += 1
        return result
    return wrapper


@log_request_duration
def get_health(request):
    log_request("/health", request.method)
    if request.method == 'GET':
        response = HttpResponse(status=200, content='OK', content_type="text/plain")
    else:
        response = HttpResponse(status=400)

    return response


def todo_creating(request, response):
    verbal_response = {}
    verbal_request_body = json.loads(request.body)

    outcome = todos.append(verbal_request_body['title'], verbal_request_body['content'], verbal_request_body['dueDate'])
    if outcome == "title already exists":
        verbal_response["errorMessage"] = f"Error: TODO with the title {verbal_request_body['title']} already exists in the system"
        todo_logger.error(f"Error: TODO with the title {verbal_request_body['title']} already exists in the system | request #{global_request_counter}")
        response.status_code = 409
    elif outcome == "due date is in the past":
        verbal_response["errorMessage"] = "Error: Can’t create new TODO that its due date is in the past"
        todo_logger.error(f"Error: TODO with the title {verbal_request_body['title']} already exists in the system | request #{global_request_counter}")
        response.status_code = 409
    else:
        todo_logger.info(f"Creating new TODO with Title [{verbal_request_body['title']}] | request #{global_request_counter}")
        todo_logger.debug(f"Currently there are {todos.get_total_todos()-1} TODOs in the system. New TODO will be assigned with id {todos.get_avail_id()-1} | request #{global_request_counter}")
        verbal_response["result"] = int(outcome)
        response.status_code = 200

    response.content = json.dumps(verbal_response)


def check_outcome(outcome, response, query_id):
    verbal_response = {}

    if outcome == 'no such TODO':
        verbal_response["errorMessage"] = f"Error: no such TODO with id {query_id} | request #{global_request_counter}"
        todo_logger.debug(f"Error: no such TODO with id {query_id} | request #{global_request_counter} | request #{global_request_counter}")
        response.status_code = 404
    else:
        verbal_response["result"] = outcome
        response.status_code = 200

    response.content = json.dumps(verbal_response)


def todo_updating(request, response):
    query_id = int(request.GET['id'])
    query_status = request.GET['status']

    if query_status == 'PENDING' or query_status == 'LATE' or query_status == 'DONE':
        todo_logger.info(f"Update TODO id [{query_id}] state to {query_status} | request #{global_request_counter}")
        todo_logger.debug(f"Todo id [{query_id}] state change: {todos.get_status_of_todo(query_id)} --> {query_status} | request #{global_request_counter}")
        outcome = todos.update(query_id, query_status)
        check_outcome(outcome, response, query_id)
    else:
        response.status_code = 400


def todo_deleting(request, response):
    query_id = int(request.GET['id'])
    outcome = todos.delete(query_id)
    if outcome != 'no such TODO':
        todo_logger.info(f"Removing todo id {query_id} | request #{global_request_counter}")
        todo_logger.debug(f"After removing todo id [{query_id}] there are {todos.get_total_todos()} TODOs in the system | request #{global_request_counter}")
    check_outcome(outcome, response, query_id)


@log_request_duration
def general_todo(request):
    response = HttpResponse()
    log_request('/todo', request.method)

    if request.method == 'POST':  # create a new TODO
        todo_creating(request, response)
    elif request.method == 'PUT':  # Update TODO status
        todo_updating(request, response)
    elif request.method == 'DELETE':  # Delete TODO
        todo_deleting(request, response)
    else:
        response.status_code = 400

    return response


@log_request_duration
def get_total_todo(request):
    response = HttpResponse()

    log_request('/todo/size', request.method)
    req_status = request.GET['status']

    if req_status == 'ALL' or req_status == 'PENDING' or req_status == 'LATE' or req_status == 'DONE':
        total_todos = todos.count_by_status(req_status)
        response.content = json.dumps({"result": total_todos})
        response.status_code = 200
        todo_logger.info(f"Total TODOs count for state {req_status} is {total_todos} | request #{global_request_counter}")
    else:
        response.status_code = 400

    return response


@log_request_duration
def get_todo_data(request):
    response = HttpResponse()

    log_request('/todo/content', request.method)
    query_params = request.GET

    if (request.method == 'GET') and ('status' in query_params.keys()):
        # filtering according to status
        if query_params['status'] != 'ALL':
            filtered_todos = todos.filter_todos(query_params['status'])
        else:
            filtered_todos = todos
        # sorting according to sortBy
        if 'sortBy' not in query_params.keys():
            list_of_sorted_todos = filtered_todos.sort_todos_by_sort_by('ID')
            todo_logger.info(
                f"Extracting todos content. Filter: {query_params['status']} | Sorting by: ID | request #{global_request_counter}")
        else:
            list_of_sorted_todos = filtered_todos.sort_todos_by_sort_by(query_params['sortBy'])
            todo_logger.info(
                f"Extracting todos content. Filter: {query_params['status']} | Sorting by: {query_params['sortBy']} | request #{global_request_counter}")
        # converting each item on the sorted list to dict and append it to final list
        if len(list_of_sorted_todos) == 0:  # if sortBy is not accurate or previous methods have failed
            response.status_code = 400
        else:
            list_of_json_todos = []
            for todo in list_of_sorted_todos:
                list_of_json_todos.append(todo.get_todo_as_dict())
            response.content = json.dumps({"result": list_of_json_todos})
            response.status_code = 200
            todo_logger.debug(f"There are a total of {todos.get_total_todos()} todos in the system. The result holds {len(list_of_sorted_todos)} todos | request #{global_request_counter}")
    else:
        response.status_code = 400

    return response


@log_request_duration
def manage_logs(request):
    response = HttpResponse()
    query_params = request.GET

    log_request('/logs/level', request.method)
    if request.method == 'GET':
        get_current_level_of_logger(request, response, query_params['logger-name'])
    elif request.method == 'PUT':
        set_current_level_of_logger(request, response, query_params)
    else:
        response.status_code = 400

    return response


def get_current_level_of_logger(request, response, logger_name):
    if logger_name == 'request-logger':
        response.content = request_logger_level
        response.status_code = 200
    elif logger_name == 'todo-logger':
        response.content = todo_logger_level
        response.status_code = 200
    else:
        response.content = "FAIL"
        response.status_code = 400


def set_current_level_of_logger(request, response, query_params):
    logger_name = query_params['logger-name']
    global request_logger_level
    global todo_logger_level
    global todo_logger_id

    if logger_name == 'request-logger':
        if is_level_valid(query_params['logger-level']):
            request_logger.remove(request_logger_id[0])
            request_logger.remove(request_logger_id[1])
            request_logger_id.clear()
            request_logger_level = query_params['logger-level']
            request_logger_id.append(logger.add(stdout, level=request_logger_level,
                                                format="{time:DD-MM-YYYY HH:mm:ss.SSS} {level}: {message}",
                                                filter=make_filter("request_logger")))
            request_logger_id.append(logger.add("logs/requests.log", level=request_logger_level,
                                                format="{time:DD-MM-YYYY HH:mm:ss.SSS} {level}: {message}",
                                                filter=make_filter("request_logger")))
            response.content = query_params['logger-level']
            response.status_code = 200
        else:
            response.content = "FAIL"
            response.status_code = 400
    elif logger_name == 'todo-logger':
        if is_level_valid(query_params['logger-level']):
            todo_logger_level = query_params['logger-level']
            todo_logger.remove(todo_logger_id)
            todo_logger_id = logger.add("logs/todos.log", level=todo_logger_level,
                                        format="{time:DD-MM-YYYY HH:mm:ss.SSS} {level}: {message}",
                                        filter=make_filter("todo_logger"))
            response.content = query_params['logger-level']
            response.status_code = 200
        else:
            response.content = "FAIL"
            response.status_code = 400
    else:
        response.content = "FAIL"
        response.status_code = 400


def is_level_valid(logger_level):
    if logger_level == 'DEBUG' or logger_level == 'INFO' or logger_level == 'ERROR':
        return True
    else:
        return False

