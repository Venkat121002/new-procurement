import requests
from django.http import JsonResponse

def get_method_without_token(request,url):
    response = requests.get(url)
    data = response.json()
    return JsonResponse(data, safe=False)

def get_method_with_token(request,url,token):
    headers = {
        "Authorization": "Token your_token_here"
    }
    response = requests.get(url, headers=headers)
    data = response.json()
    return JsonResponse(data, safe=False)

def post_method_with_token(request, url, token, post_data):
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=post_data, headers=headers)
    try:
        data = response.json()
    except ValueError:
        data = {"error": "Invalid JSON response from server"}

    return JsonResponse(data, safe=False, status=response.status_code)


def post_method_without_token(request, url, post_data):
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=post_data, headers=headers)

    try:
        data = response.json()
    except ValueError:
        data = {"error": "Invalid JSON response from server"}

    return JsonResponse(data, safe=False, status=response.status_code)
