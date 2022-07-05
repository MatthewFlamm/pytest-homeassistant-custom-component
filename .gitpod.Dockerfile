FROM gitpod/workspace-python-3.9

USER gitpod

RUN pip install -r requirements_generate.txt
RUN pip install -e .