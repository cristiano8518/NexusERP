from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        payload = {
            "success": False,
            "errors": response.data,
        }
        if isinstance(response.data, dict) and "detail" in response.data:
            payload["message"] = response.data["detail"]
        response.data = payload
    return response
