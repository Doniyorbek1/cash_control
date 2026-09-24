from aiogram.fsm.state import State, StatesGroup

class AddExpenseState(StatesGroup):
    select_category = State()
    enter_amount = State()
    enter_description = State()
    confirm = State()

class AddIncomeState(StatesGroup):
    select_category = State()
    enter_amount = State()
    enter_description = State()
    confirm = State()

class AddCategoryState(StatesGroup):
    select_type = State()
    enter_name = State()

class AddTaskState(StatesGroup):
    enter_title = State()

class AddReminderState(StatesGroup):
    enter_text = State()
    enter_time = State()