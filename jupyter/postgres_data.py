import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

load_dotenv()

Base = declarative_base()

class ProbeRequest(Base):
    __tablename__ = 'probe_requests'
    __bind_key__ = 'probe_request'

    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    macaddress = Column(String)
    make = Column(String)
    ssid = Column(String)
    rssi = Column(Integer)

    def __repr__(self):
        return (
            "<ProbeRequest(id={self.id}, "
            f"date={self.date}, "
            f"macaddress={self.macaddress}, "
            f"make='{self.make}', "
            f"ssid='{self.ssid}', "
            f"rssi={self.rssi})>"
        )
    
    def to_dict(self):
        return {
            'date': self.date,
            'macaddress': self.macaddress,
            'make': self.make,
            'ssid': self.ssid,
            'rssi': self.rssi,
        }


db = create_engine("postgres://{user}:{password}@{host}:{port}/{database}".format(
    host=os.getenv("SQL_HOST", ""),
    port=os.getenv("SQL_PORT", 5432),
    database="probes",
    user=os.getenv("SQL_USER", ""),
    password=os.getenv("SQL_PASSWORD", "")
))

Base.metadata.create_all(db)
Session = sessionmaker(bind=db)


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


def get_data():
    with session_scope() as s:
        data = pd.read_sql(
            s.query(ProbeRequest).order_by(ProbeRequest.date.desc()).limit(100000).statement,
            s.bind,
            parse_dates=['date']
        )
    return data
