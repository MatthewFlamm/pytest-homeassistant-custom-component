FROM gitpod/workspace-python-3.10

USER gitpod
COPY requirements_generate.txt requirements_generate.txt
RUN pip install -r requirements_generate.txt
