from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class ScheduleLiveStates(StatesGroup):
    choosing_course = State()
    entering_datetime = State()


class BroadcastStates(StatesGroup):
    choosing_target = State()
    choosing_mentor = State()
    choosing_mentor_course = State()
    waiting_for_message = State()
    confirming = State()


class MentorBroadcastStates(StatesGroup):
    choosing_target = State()
    waiting_for_message = State()
    confirming = State()


class AddQuotaStates(StatesGroup):
    choosing_mentor = State()
    choosing_course = State()
    entering_amount = State()
