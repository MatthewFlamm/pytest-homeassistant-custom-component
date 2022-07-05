FROM gitpod/workspace-python-3.9

USER gitpod
COPY requirements_generate.txt requirements_generate.txt
COPY setup.py setup.py
RUN pip install -r requirements_generate.txt
RUN pip install -e .