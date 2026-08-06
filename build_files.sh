#!/bin/bash
pip install -r requirements.txt --break-system-packages
rm -rf staticfiles
python manage.py collectstatic --noinput