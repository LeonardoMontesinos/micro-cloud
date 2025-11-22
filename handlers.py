import json
import boto3
import os
import uuid
from datetime import datetime
from utils_response import ok, error
from auth_helper import validate_admin_access

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['PRODUCTOS_TABLE'])

def create_product(event, context):
    # 1. Validación de Seguridad (Reutilizable)
    user, err_response = validate_admin_access(event)
    if err_response:
        return err_response

    # 2. Lógica de Negocio
    try:
        tenant_id = user.get("tenant") # Extraído del token validado
        if not tenant_id:
             return error("Token missing tenant information", 400)

        data = json.loads(event['body'])
        product_id = f"PROD-{str(uuid.uuid4())[:8]}"

        item = {
            'tenant_id': tenant_id,
            'producto_id': product_id,
            'nombre': data.get('nombre'),
            'categoria': data.get('categoria'),
            'descripcion': data.get('descripcion'),
            'precio': str(data.get('precio')), # Decimales como string para evitar errores de float en Dynamo
            'created_at': datetime.now().isoformat()
        }

        table.put_item(Item=item)
        
        return ok({'message': 'Producto creado', 'id': product_id}, 201)

    except Exception as e:
        print(e)
        return error(str(e), 500)

def update_product(event, context):
    user, err_response = validate_admin_access(event)
    if err_response: return err_response

    try:
        tenant_id = user.get("tenant")
        product_id = event['pathParameters']['id']
        data = json.loads(event['body'])

        # Construcción dinámica del Update
        update_expression = "set "
        expression_values = {}
        expression_names = {}

        for key, value in data.items():
            update_expression += f"#{key} = :{key}, "
            expression_values[f":{key}"] = str(value) if isinstance(value, float) else value
            expression_names[f"#{key}"] = key

        update_expression = update_expression.rstrip(", ")

        table.update_item(
            Key={'tenant_id': tenant_id, 'producto_id': product_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values,
            ExpressionAttributeNames=expression_names
        )

        return ok({'message': 'Producto actualizado'})
    except Exception as e:
        return error(str(e), 500)

def delete_product(event, context):
    user, err_response = validate_admin_access(event)
    if err_response: return err_response

    try:
        tenant_id = user.get("tenant")
        product_id = event['pathParameters']['id']

        table.delete_item(
            Key={'tenant_id': tenant_id, 'producto_id': product_id}
        )

        return ok({'message': 'Producto eliminado'})
    except Exception as e:
        return error(str(e), 500)
