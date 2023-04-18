FROM python:3.11-slim-bullseye

# install app dependencies
RUN pip install flask==2.2.* requests waitress

# Install app
COPY KosmikAutoUpdateServer/* /Kosmik/
EXPOSE 8080

CMD python3 /Kosmik/__main__.py
