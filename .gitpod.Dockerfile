FROM gitpod/workspace-python-3.11

USER gitpod
COPY requirements_generate.txt requirements_generate.txt
RUN pip install -r requirements_generate.txt
