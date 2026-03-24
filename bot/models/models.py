from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, JSON, ForeignKey, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from bot.models.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    timezone = Column(String, nullable=False, default="UTC")
    reminder_interval_hours = Column(Integer, nullable=False, default=2)
    morning_lock_minutes = Column(Integer, nullable=False, default=30)
    wake_up_time = Column(String, nullable=True)  # stored as "HH:MM"
    alter_ego = Column(String, nullable=False, default="Champion")
    silent_mode = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)

    plans = relationship("Plan", back_populates="user")
    daily_logs = relationship("DailyLog", back_populates="user")
    weekly_analytics = relationship("WeeklyAnalytics", back_populates="user")

class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    categories = Column(JSON, nullable=False)  # list of {name, tasks: [{name, target}]}
    rules = Column(JSON, nullable=False)      # list of strings
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="plans")

class DailyLog(Base):
    __tablename__ = "daily_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    tasks = Column(JSON, nullable=False)        # list of {name, category, target, progress, status, completed_before_bedtime}
    rule_violations = Column(JSON, default=list)
    morning_confirmed = Column(Boolean, default=False)
    morning_late = Column(Boolean, default=False)
    wake_up_time = Column(String, nullable=True)   # "HH:MM"
    bedtime = Column(String, nullable=True)
    discipline_score = Column(Integer, nullable=True)
    sleep_duration_hours = Column(Float, nullable=True)
    weak_start = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="daily_logs")

class WeeklyAnalytics(Base):
    __tablename__ = "weekly_analytics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    week_start = Column(Date, nullable=False)
    avg_score = Column(Float, nullable=True)
    most_missed_tasks = Column(JSON, default=list)  # list of {name, miss_count}
    weak_time_period = Column(String, nullable=True)
    sleep_score = Column(Integer, nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="weekly_analytics")