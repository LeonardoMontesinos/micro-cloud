import boto3
import json
import os
from utils_response import error

AUTH_LAMBDA_NAME = os.environ.get("AUTH_LAMBDA_NAME", "auth-microservice-dev-validateToken")
lambda_client = boto3.client("lambda")

def invoke_token_validator(token):
    payload = json.dumps({"token": token})

    try:
        response = lambda_client.invoke(
            FunctionName=AUTH_LAMBDA_NAME,
            InvocationType="RequestResponse",
            Payload=payload
        )
        
        payload_stream = response["Payload"]
        return json.loads(payload_stream.read())
    except Exception as e:
        print(f"Error invocando validador: {str(e)}")
        return {"statusCode": 500, "body": "Internal Auth Error"}

def validate_admin_access(event):
    """
    Valida headers, invoca lambda externa y verifica rol admin.
    Retorna (UserDict, None) si es exitoso.
    Retorna (None, ErrorResponse) si falla.
    """
    headers = event.get("headers", {}) or {}
    # Manejo de mayúsculas/minúsculas en headers
    auth = headers.get("Authorization") or headers.get("authorization")

    if not auth:
        return None, error("Missing Authorization header", 401)

    token = auth.replace("Bearer ", "").strip()

    # Invocar al microservicio de Auth
    validation = invoke_token_validator(token)

    # Verificar si la lambda de auth respondió 200 OK
    if validation.get("statusCode") != 200:
        return None, error("Forbidden - Token invalido o expirado", 403)

    # Parsear el body que viene como string JSON dentro de la respuesta de Lambda
    try:
        user = json.loads(validation["body"])
    except:
        # Si el body ya venía como dict (depende de tu implementación exacta de auth)
        user = validation["body"] if isinstance(validation["body"], dict) else {}

    # Reglas de Negocio
    if user.get("type") != "worker":
        return None, error("Only workers allowed", 403)

    if user.get("role") != "admin":
        return None, error("Admin role required", 403)
        
    return user, None
