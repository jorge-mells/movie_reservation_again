## 📝 Table of Contents
- [About](#about)
- [Getting Started](#getting_started)
- [Deployment](#deployment)
- [Usage](#usage)
- [Built Using](#built_using)
- [TODO](../TODO.md)
- [Contributing](../CONTRIBUTING.md)
- [Authors](#authors)
- [Acknowledgments](#acknowledgement)

## 🧐 About <a name = "about"></a>
An intermediate movie reservation system PoC using fastapi to practice basic backend and devops practices such as the following:
- Robust Error Handling
- Unit and Integration Testing
- A simple CI/CD pipeline with webhooks for deployment
- Centralised configuration management
- Database migrations
- Using ORMs
- Database Seeding
- User Authentication with JWT


## 🏁 Getting Started <a name = "getting_started"></a>
These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See [deployment](#deployment) for notes on how to deploy the project on a live system.

### Prerequisites
Install python and uv([install uv](https://docs.astral.sh/uv/getting-started/installation/)) to get started

### Installing
A step by step series of examples that tell you how to get a development env running.

Copy the relevant environment variables from `.env.example` to `.env`. At the very minimum copy SECRET_KEY. If you don't want to use the test db, make sure to set DATABASE_URL.

```
echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env'
```

Migrate the database

```
uv run alembic upgrade head
```

Start the development server
```
uv run fastapi dev
```

Try it with the following(replace 8000 with your actual port) or open a browser and type `localhost:8000` in the address bar:
```
curl http://localhost:8000
-> {"message":"see /docs for usage"}
```

## 🔧 Running the tests <a name = "tests"></a>
Running tests is straightfoward. Use the following:
```
uv run pytest
```

If you want to run with coverage(needed if you intend to push changes later on):
```
uv run pytest --cov=.
```

Use pre-commit to check linting and types

```
uv run pre-commit run --all-files
```

## 🚀 Deployment <a name = "deployment"></a>
See [movie_reservation_deployment](https://github.com/jorge-mells/movie_reservation_deployment) for a guide on how to deploy securely on hetzner cloud with a mysql db

## ⛏️ Built Using <a name = "built_using"></a>
- [FastAPI](https://fastapi.tiangolo.com/) - Web Framework
- [SQLModel](https://sqlmodel.tiangolo.com/) - Database ORM & Modeling
- [Alembic](https://alembic.sqlalchemy.org/) - Database Migrations
- [PyMySQL](https://github.com/PyMySQL/PyMySQL) - MySQL Database Driver
- [PyJWT](https://pyjwt.readthedocs.io/) - Token-based Authentication
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) - Configuration Management
- [Ruff](https://astral.sh/ruff) - Linter & Code Formatter
- [Pytest](https://docs.pytest.org/) - Testing Framework

## ✍️ Authors <a name = "authors"></a>
- [@jorge-mells](https://github.com/jorge-mells) - Idea & Initial work

See also the list of [contributors](https://github.com/jorge-mells/movie_reservation_again/contributors) who participated in this project.

## 🎉 Acknowledgements <a name = "acknowledgement"></a>
- Gemini
- Chatgpt
- Claude
