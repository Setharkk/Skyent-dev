import asyncio
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool
from sqlalchemy.ext.asyncio import async_engine_from_config

# Ajuster sys.path pour inclure le répertoire racine du projet backend
# Cela permet à Alembic de trouver les modules de l'application (app.db.base, app.config)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import settings # Importer les paramètres de configuration
from app.db.base import Base  # Importer la classe Base de vos modèles

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpréter le fichier de configuration pour le support de la journalisation Python.
# Cette ligne configure essentiellement les loggers.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ajouter le MetaData de votre modèle pour le support de l'autogenerate
target_metadata = Base.metadata

# Définir l'URL de la base de données à partir des paramètres de configuration
effective_db_url = settings.database_url
if settings.test_database:
    # En mode test, on pourrait vouloir une URL spécifique pour Alembic.
    # Pour l'instant, on utilise la même.
    # Exemple: effective_db_url = "sqlite+aiosqlite:///./test_alembic.db"
    pass
config.set_main_option("sqlalchemy.url", effective_db_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

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


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    """In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # Important pour l'async avec Alembic
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    if os.environ.get("ALEMBIC_CONTEXT") == "SYNC":
        sync_engine_url = settings.database_url
        if sync_engine_url.startswith("sqlite+aiosqlite"):
            sync_engine_url = sync_engine_url.replace("sqlite+aiosqlite", "sqlite")
        
        sync_engine = create_engine(sync_engine_url)
        with sync_engine.connect() as connection:
            do_run_migrations(connection)
        sync_engine.dispose()
    else:
        try:
            asyncio.run(run_async_migrations())
        except RuntimeError as e:
            if "cannot be called from a running event loop" in str(e):
                print(
                    "Tentative d'exécution des migrations asynchrones depuis une boucle d'événements existante. "
                    "Cela peut ne pas fonctionner comme prévu sans configuration supplémentaire (ex: nest_asyncio). "
                    "Si vous exécutez une commande Alembic qui ne nécessite pas de connexion async (ex: history, current), "
                    "essayez de définir la variable d'environnement ALAMBIC_CONTEXT=SYNC."
                )
            raise e


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
