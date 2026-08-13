import io
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from database.models import Transaction, Category, TransactionType

async def get_expenses_by_period(user_id: int, start_date: datetime, end_date: datetime, session: AsyncSession):
    """Kategoriyalar bo'yicha umumiy yig'indilarni olish (Grafik uchun)"""
    stmt = (
        select(Category.name, func.sum(Transaction.amount).label("total"))
        .join(Transaction, Transaction.category_id == Category.id)
        .where(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.EXPENSE,
            Transaction.created_at >= start_date,
            Transaction.created_at <= end_date
        )
        .group_by(Category.name)
    )
    result = await session.execute(stmt)
    return result.all()

async def get_detailed_transactions(user_id: int, start_date: datetime, end_date: datetime, session: AsyncSession):
    """Excel uchun barcha xarajatlarni batafsil olish"""
    stmt = (
        select(
            Transaction.created_at,
            Category.name.label("category"),
            Transaction.amount,
            Transaction.description
        )
        .join(Category, Transaction.category_id == Category.id)
        .where(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.EXPENSE,
            Transaction.created_at >= start_date,
            Transaction.created_at <= end_date
        )
        .order_by(Transaction.created_at.desc())
    )
    result = await session.execute(stmt)
    return result.all()

def generate_pie_chart(data: list[tuple[str, float]]) -> io.BytesIO:
    """Doiraviy grafik (Pie Chart) yaratish"""
    labels = [row[0] for row in data]
    amounts = [row[1] for row in data]

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(amounts, labels=labels, autopct='%1.1f%%', startangle=140)
    ax.set_title("Xarajatlar strukturasi")

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return buf

def generate_excel_report(transactions: list) -> io.BytesIO:
    """Tranzaksiyalarni chiroyli Excel jadvaliga aylantirish"""
    report_data = []
    total_amount = 0

    for row in transactions:
        created_at, category, amount, description = row
        total_amount += amount
        report_data.append({
            "Sana va vaqt": created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "Kategoriya": category,
            "Summa (so'm)": amount,
            "Izoh": description if description else "-"
        })

    # Pandas DataFrame shakllantirish
    df = pd.DataFrame(report_data)

    # Yakuniy umumiy summa qatorini qo'shish
    total_row = pd.DataFrame([{
        "Sana va vaqt": "JAMI",
        "Kategoriya": "",
        "Summa (so'm)": total_amount,
        "Izoh": ""
    }])
    df = pd.concat([df, total_row], ignore_index=True)

    buf = io.BytesIO()
    # Excel formatda saqlash
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Xarajatlar')

    buf.seek(0)
    return buf