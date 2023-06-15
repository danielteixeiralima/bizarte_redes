from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# adicione essas linhas para importar o seu objeto db
from flask import current_app
import sys
import os
sys.path.append(os.getcwd())
from app import app
app.app_context().push()
db = current_app.extensions['sqlalchemy'].db

# esta é a configuração do objeto Alembic, que provê
# acesso aos valores dentro do arquivo .ini em uso.
config = context.config

# Interprete o arquivo de configuração para o logging em Python.
# Essa linha basicamente configura os loggers.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# adicione o objeto MetaData do seu modelo aqui
# para suporte à 'autogeração'
# no seu caso, você pode fornecer o objeto MetaData através do seu objeto db SQLAlchemy
target_metadata = db.Model.metadata

# outros valores da configuração, definidos pelas necessidades de env.py,
# podem ser obtidos:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Execute migrações no modo 'offline'.

    Isso configura o contexto apenas com uma URL
    e não um Engine, embora um Engine também seja aceitável
    aqui. Ao pular a criação do Engine, nem mesmo precisamos
    que um DBAPI esteja disponível.

    Chamadas para context.execute() aqui emitem a string dada para a
    saída do script.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Execute migrações no modo 'online'.

    Neste cenário, precisamos criar um Engine
    e associar uma conexão com o contexto.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
