import json
import boto3
import csv
import io

s3 = boto3.client('s3')
sns = boto3.client('sns')

# Substitua pelo ARN do seu tópico SNS
SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:SEU_ACCOUNT_ID:csv-pipeline-notifications'

def lambda_handler(event, context):
    for record in event['Records']:
        body = json.loads(record['body'])
        bucket = body['bucket']
        key = body['key']

        print(f"🔄 Processando: {key}")

        try:
            # 1. Baixar o arquivo do S3
            response = s3.get_object(Bucket=bucket, Key=key)
            content = response['Body'].read().decode('utf-8')

            # 2. Validar o CSV
            reader = csv.DictReader(io.StringIO(content))
            rows = list(reader)
            headers = reader.fieldnames

            # Validações
            errors = []

            if len(rows) == 0:
                errors.append("Arquivo vazio — nenhuma linha de dados encontrada")

            if headers:
                for i, row in enumerate(rows, 1):
                    for header in headers:
                        if not row.get(header) or row[header].strip() == '':
                            errors.append(f"Linha {i}: campo '{header}' vazio ou nulo")

            # 3. Decidir destino
            filename = key.split('/')[-1]

            if errors:
                # FALHA — mover para /failed
                dest_key = f"failed/{filename}"
                s3.copy_object(
                    Bucket=bucket,
                    CopySource={'Bucket': bucket, 'Key': key},
                    Key=dest_key
                )
                s3.delete_object(Bucket=bucket, Key=key)

                print(f"❌ Arquivo INVÁLIDO! Movido para {dest_key}")
                print(f"   Erros encontrados: {len(errors)}")
                for e in errors:
                    print(f"   - {e}")

                # Notificar por e-mail
                sns.publish(
                    TopicArn=SNS_TOPIC_ARN,
                    Subject='❌ Pipeline CSV - Arquivo INVÁLIDO',
                    Message=f"""Arquivo com ERROS detectado no pipeline!

Arquivo: {filename}
Destino: {dest_key}
Erros encontrados: {len(errors)}

Detalhes:
{chr(10).join('- ' + e for e in errors)}

Ação necessária: Verifique o arquivo na pasta /failed do bucket {bucket}.
"""
                )

            else:
                # SUCESSO — mover para /processed
                dest_key = f"processed/{filename}"
                s3.copy_object(
                    Bucket=bucket,
                    CopySource={'Bucket': bucket, 'Key': key},
                    Key=dest_key
                )
                s3.delete_object(Bucket=bucket, Key=key)

                print(f"✅ Arquivo VÁLIDO! Movido para {dest_key}")
                print(f"   Linhas: {len(rows)}")
                print(f"   Colunas: {headers}")

                # Notificar por e-mail
                sns.publish(
                    TopicArn=SNS_TOPIC_ARN,
                    Subject='✅ Pipeline CSV - Arquivo Processado',
                    Message=f"""Arquivo processado com SUCESSO!

Arquivo: {filename}
Destino: {dest_key}
Linhas: {len(rows)}
Colunas: {', '.join(headers)}

Nenhum erro encontrado.
"""
                )

        except Exception as e:
            print(f"💥 ERRO ao processar {key}: {str(e)}")
            raise e

    return {'statusCode': 200}
