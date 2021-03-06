'''Provider interface to manipulate database.'''
import logging
from threading import local

from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from compass.utils import setting_wrapper as setting
from compass.db import model


ENGINE = create_engine(setting.SQLALCHEMY_DATABASE_URI, convert_unicode=True)
SESSION = sessionmaker(autocommit=False, autoflush=False)
SESSION.configure(bind=ENGINE)
SCOPED_SESSION = scoped_session(SESSION)
SESSION_HOLDER = local()


def init(database_url):
    '''initialize database.
    Args:
        database_url: string, database url.

    Returns:
        None
    '''
    global ENGINE
    global SCOPED_SESSION
    ENGINE = create_engine(database_url, convert_unicode=True)
    SESSION.configure(bind=ENGINE)
    SCOPED_SESSION = scoped_session(SESSION)


@contextmanager
def session():
    '''database session scope.

    To operate database, it should be called in database session.
    Example:
        with database.session() as session:
            using the session to operate the database.
    '''
    if hasattr(SESSION_HOLDER, 'session'):
        logging.error('we are already in session')
        new_session = SESSION_HOLDER.session
    else:
        new_session = SCOPED_SESSION()
    try:
        SESSION_HOLDER.session = new_session
        yield new_session
        new_session.commit()
    except Exception as error:
        new_session.rollback()
        logging.error('failed to commit session')
        logging.exception(error)
        raise error
    finally:
        new_session.close()
        SCOPED_SESSION.remove()
        del SESSION_HOLDER.session


def current_session():
    '''Get the current session scope when it is called.

    Return:
        database session.

    Exceptions:
        Exception indicates the function is called out of session scope.
    '''
    try:
        return SESSION_HOLDER.session
    except Exception as error:
        logging.error('It is not in the session scope')
        logging.exception(error)
        raise error


def create_db():
    '''Create database'''
    model.BASE.metadata.create_all(bind=ENGINE)


def drop_db():
    '''Drop database.'''
    model.BASE.metadata.drop_all(bind=ENGINE)


def create_table(table):
    '''Create table.
    
    Args:
        table: Class of the Table defined in the model.
    
    Returns:
        None
    '''
    table.__table__.create(bind=ENGINE, checkfirst=True)


def drop_table(table):
    '''Drop table.

    Args:
        table: Class of the Table defined in the model.

    Returns:
        None
    '''
    table.__table__.drop(bind=ENGINE, checkfirst=True)    
