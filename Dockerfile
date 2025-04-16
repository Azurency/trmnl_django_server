FROM python:3.13

WORKDIR /src

# Add UV
COPY --from=ghcr.io/astral-sh/uv:0.6.6 /uv /uvx /bin/

# done first so we can cache dependencies between code changes
COPY . .
RUN uv sync --frozen
ENV PATH="/src/.venv/bin:$PATH"
RUN ls -al

#RUN apt-get update && apt-get install -y nginx && apt-get clean && rm -rf /var/lib/apt/lists/*
#
#COPY etc/nginx.conf /etc/nginx/sites-available/default

RUN python manage.py collectstatic --noinput

EXPOSE 8000

# Command to run
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
