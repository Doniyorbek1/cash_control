from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from sqlalchemy.ext.asyncio import AsyncSession
from services.reports import (
    get_expenses_by_period, 
    get_detailed_transactions, 
    generate_pie_chart, 
    generate_excel_report
)
from keyboards.reports_kb import get_reports_keyboard

reports_router = Router()

@reports_router.message(F.text == "📊 Hisobotlar")
async def cmd_reports(message: Message):
    await message.answer(
        "<b>📊 Hisobotlar bo'limi:</b>\n\n"
        "Qaysi vaqt oralig'i uchun xarajatlar tahlili va Excel hisobotini olmoqchisiz?",
        parse_mode="HTML",
        reply_markup=get_reports_keyboard()
    )

@reports_router.callback_query(F.data.startswith("report_"))
async def process_report_selection(callback: CallbackQuery, db_session: AsyncSession):
    now = datetime.utcnow()
    period = callback.data.split("_")[1]

    if period == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        period_title = "Bugungi"
        filename_prefix = "bugungi"
    elif period == "week":
        start_date = now - timedelta(days=now.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        period_title = "Haftalik"
        filename_prefix = "haftalik"
    elif period == "month":
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        period_title = "Oylik"
        filename_prefix = "oylik"
    else:
        await callback.answer("Noma'lum oraliq!", show_alert=True)
        return

    # 1. Grafikli hisobot uchun yig'indi ma'lumotlar
    summary_data = await get_expenses_by_period(callback.from_user.id, start_date, now, db_session)

    if not summary_data:
        await callback.message.edit_text(
            f"ℹ️ <b>{period_title}</b> oraliqda hech qanday xarajat topilmadi.",
            parse_mode="HTML",
            reply_markup=get_reports_keyboard()
        )
        await callback.answer()
        return

    total_sum = sum(row[1] for row in summary_data)
    text = f"<b>📊 {period_title} xarajatlar hisoboti:</b>\n\n"

    for cat_name, amount in summary_data:
        percentage = (amount / total_sum) * 100
        text += f"• <b>{cat_name}:</b> {amount:,.2f} so'm (<i>{percentage:.1f}%</i>)\n"

    text += f"\n<b>💰 Jami xarajat:</b> {total_sum:,.2f} so'm"

    # 2. Grafik va Excel faylni generatsiya qilish
    chart_buffer = generate_pie_chart(summary_data)
    photo = BufferedInputFile(chart_buffer.read(), filename="report.png")

    detailed_transactions = await get_detailed_transactions(callback.from_user.id, start_date, now, db_session)
    excel_buffer = generate_excel_report(detailed_transactions)
    document = BufferedInputFile(
        excel_buffer.read(), 
        filename=f"xarajatlar_{filename_prefix}_{now.strftime('%Y%m%d')}.xlsx"
    )

    # Avvalgi menyu xabarini o'chirib, natijalarni yuboramiz
    await callback.message.delete()
    
    # Rasm va matnli hisobot
    await callback.message.answer_photo(
        photo=photo,
        caption=text,
        parse_mode="HTML"
    )
    
    # Excel hujjatini yuborish
    await callback.message.answer_document(
        document=document,
        caption=f"📁 <b>{period_title} batafsil Excel hisoboti</b>",
        parse_mode="HTML"
    )
    await callback.answer()