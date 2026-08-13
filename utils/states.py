from aiogram.fsm.state import State, StatesGroup

class AddExpenseState(StatesGroup):
    select_category = State()
    enter_amount = State()
    enter_description = State()  # Izoh kiritish uchun (ixtiyoriy)
    confirm = State()            # Tasdiqlash bosqichi

class AddCategoryState(StatesGroup):
    enter_name = State()

class AddTaskState(StatesGroup):
    enter_title = State()

class AddReminderState(StatesGroup):
    enter_text = State()  # Eslatma matni
    enter_time = State()  # Sana va vaqt (Masalan: 2026-08-10 18:30 yoki 18:30)