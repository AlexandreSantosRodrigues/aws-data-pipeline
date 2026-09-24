import json
import urllib.parse
import boto3

sqs = boto3.client('sqs')

# Substitua pela URL da sua fila SQS
QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/SEU_ACCOUNT_ID/csv-processing-queue'

def lambda_handler(event, context):
    record = event['Records'][0]
    bucket = record['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(record['s3']['object']['key'])
    size = record['s3']['object'].get('size', 0)

    print(f"📥 Novo arquivo detectado!")
    print(f"   Bucket: {bucket}")
    print(f"   Arquivo: {key}")
    print(f"   Tamanho: {size} bytes")

    message = {
        'bucket': bucket,
        'key': key,
        'size': size
    }

    sqs.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody=json.dumps(message)
    )

    print(f"📤 Mensagem enviada para SQS com sucesso!")

    return {
        'statusCode': 200,
        'body': json.dumps('Mensagem enviada para SQS!')
    }
