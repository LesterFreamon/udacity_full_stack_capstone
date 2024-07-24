from io import BytesIO
import logging

logging.basicConfig(level=logging.INFO)

def upload_file_to_s3(s3_client, file, filename, bucket_name):
    """Upload a file to an S3 bucket."""
    try:
        s3_client.upload_fileobj(
            file,
            bucket_name,
            filename,
            ExtraArgs={
                "ContentType": "image/jpeg"
            }
        )
    except Exception as e:
        print("Something Happened: ", e)
        return e
    return f"https://{bucket_name}.s3.amazonaws.com/{filename}"


def download_file_from_s3(s3_client, filename, bucket_name):
    try:
        file_obj = BytesIO()
        s3_client.download_fileobj(bucket_name, filename, file_obj)
        file_obj.seek(0)
        return file_obj
    except Exception as e:
        logging.error("Something happened: %s", e)
        return None


def delete_file_from_s3(s3_client, filename, bucket_name):
    """Delete a file from an S3 bucket."""
    try:
        s3_client.delete_object(Bucket=bucket_name, Key=filename)
    except Exception as e:
        logging.error("Something happened: %s", e)
        return str(e)
    return None

