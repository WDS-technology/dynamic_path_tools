from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class DroneStation(Base):
    __tablename__ = "drone_stations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    station_name = Column(String(100), unique=True, nullable=False)

    position_x = Column(Float, nullable=False)
    position_y = Column(Float, nullable=False)
    position_z = Column(Float, nullable=False)


class Obstacle(Base):
    __tablename__ = "obstacles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)

    position_x = Column(Float, nullable=False)
    position_y = Column(Float, nullable=False)
    position_z = Column(Float, nullable=False)

    width = Column(Float, nullable=False)
    depth = Column(Float, nullable=False)
    height = Column(Float, nullable=False)


class NavigationWaypoint(Base):
    __tablename__ = "navigation_waypoints"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    passage_id = Column(String(50), nullable=False)
    order = Column(Integer, nullable=False)

    position_x = Column(Float, nullable=False)
    position_y = Column(Float, nullable=False)
    position_z = Column(Float, nullable=False)

    is_intersection = Column(Boolean, nullable=False, default=False)
    is_entrance = Column(Boolean, nullable=False, default=False)
