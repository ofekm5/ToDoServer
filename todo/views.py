from django.http import HttpResponse
from . import utils
import json


todos = utils.Todos()


def get_health(request):
    if request.method == 'GET':
        return HttpResponse(status=200, content='OK', content_type="text/plain")
    else:
        return HttpResponse(status=400)


def todo_creating(request, response):
    verbal_response = {}
    verbal_request_body = json.loads(request.body)

    outcome = todos.append(verbal_request_body['title'], verbal_request_body['content'], verbal_request_body['dueDate'])
    if outcome == "title already exists":
        verbal_response["errorMessage"] = f"Error: TODO with the title {verbal_request_body['title']} already exists in the system"
        response.status_code = 409
    elif outcome == "due date is in the past":
        verbal_response["errorMessage"] = "Error: Can’t create new TODO that its due date is in the past"
        response.status_code = 409
    else:
        verbal_response["result"] = int(outcome)
        response.status_code = 200

    response.content = json.dumps(verbal_response)


def check_outcome(outcome, response, query_id):
    verbal_response = {}

    if outcome == 'no such TODO':
        verbal_response["errorMessage"] = f"Error: no such TODO with id {query_id}"
        response.status_code = 404
    else:
        verbal_response["result"] = outcome
        response.status_code = 200

    response.content = json.dumps(verbal_response)


def todo_updating(request, response):
    query_id, query_status = int(request.GET['id']), request.GET['status']

    if query_status == 'PENDING' or query_status == 'LATE' or query_status == 'DONE':
        outcome = todos.update(query_id, query_status)
        check_outcome(outcome, response, query_id)
    else:
        response.status_code = 400


def todo_deleting(request, response):
    query_id = int(request.GET['id'])
    outcome = todos.delete(query_id)
    check_outcome(outcome, response, query_id)


def general_todo(request):
    response = HttpResponse()

    if request.method == 'POST':  # create a new TODO
        todo_creating(request, response)
    elif request.method == 'PUT':  # Update TODO status
        todo_updating(request, response)
    elif request.method == 'DELETE':  # Delete TODO
        todo_deleting(request, response)
    else:
        response.status_code = 400

    return response


def get_total_todo(request):
    response = HttpResponse()
    req_status = request.GET['status']

    if req_status == 'ALL' or req_status == 'PENDING' or req_status == 'LATE' or req_status == 'DONE':
        response.content = json.dumps({"result": todos.count_by_status(req_status)})
        response.status_code = 200
    else:
        response.status_code = 400

    return response


def get_todo_data(request):
    response = HttpResponse()
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
        else:
            list_of_sorted_todos = filtered_todos.sort_todos_by_sort_by(query_params['sortBy'])
        # converting each item on the sorted list to dict and append it to final list
        if len(list_of_sorted_todos) == 0:  # if sortBy is not accurate or previous methods have failed
            response.status_code = 400
        else:
            list_of_json_todos = []
            for todo in list_of_sorted_todos:
                list_of_json_todos.append(todo.get_todo_as_dict())
            response.content = json.dumps({"result": list_of_json_todos})
            response.status_code = 200
    else:
        response.status_code = 400

    return response
