FROM python:3.12

RUN mkdir /app
WORKDIR /app

COPY ./requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt "arkitekt[all]>=6.6.0" "mikro[table]>=8.0.0"

# The whole project: the app target may be any module in it, not only app.py.
COPY . /app

# Bake the scikit-image sample data in, so Generate Test Image works offline
RUN python init.py
