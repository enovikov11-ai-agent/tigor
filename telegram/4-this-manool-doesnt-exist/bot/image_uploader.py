import sqlite3
import boto3
import os
import shutil

DATABASE_URL = 'database.sqlite'
BUCKET_NAME = 'manool'
IMAGES_FOLDER = 'images/'
DONE_FOLDER = 'done/'

def connect_to_database():
    connection = sqlite3.connect(DATABASE_URL)
    return connection

def create_database_table():
    connection = connect_to_database()
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS images (
            url text PRIMARY KEY,
            used boolean DEFAULT false
        )
    """)
    connection.commit()

def upload_to_s3(image_path):
    s3 = boto3.client('s3',endpoint_url="https://storage.yandexcloud.net/")
    s3.upload_file(image_path, BUCKET_NAME, image_path)
    return f"https://manool.website.yandexcloud.net/{image_path}"

def add_image_to_database(url):
    connection = connect_to_database()
    cursor = connection.cursor()
    cursor.execute("INSERT INTO images (url, used) VALUES (?,?)", (url, False))
    connection.commit()

def initialize_database():
    create_database_table()
    for image in os.listdir(IMAGES_FOLDER):
        image_path = os.path.join(IMAGES_FOLDER, image)
        url = upload_to_s3(image_path)
        add_image_to_database(url)
        shutil.move(image_path, os.path.join(DONE_FOLDER, image))

if __name__ == '__main__':
    initialize_database()
