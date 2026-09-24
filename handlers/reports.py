from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from sqlalchemy.ext.asyncio import AsyncSession
from services.reports import (
    get_financial_summary_by_period,
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
        "Qaysi vaqt oralig'i uchun moliyaviy tahlil va Excel hisobotini olmoqchisiz?",
        parse_mode="HTML",
        reply_markup=get_reports_keyboard()
    )

@reports_router.callback_query(F.data.startswith("report_"))
async def process_report_selection(callback: CallbackQuery, db_session: AsyncSession):
    now = datetime.utcnow()
    
    # "report_today" -> "today", "report_week" -> "week", "report_month" -> "month"
    period = callback.data.replace("report_", "").strip()

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
        await callback.answer(f"Noma'lum oraliq: {period}", show_alert=True)
        return

    # 1. Moliyaviy sarhisob (Kirim, Chiqim, Balans)
    summary = await get_financial_summary_by_period(callback.from_user.id, start_date, now, db_session)
    detailed_transactions = await get_detailed_transactions(callback.from_user.id, start_date, now, db_session)

    if not detailed_transactions:
        await callback.message.edit_text(
            f"ℹ️ <b>{period_title}</b> oraliqda hech qanday amaliyot topilmadi.",
            parse_mode="HTML",
            reply_markup=get_reports_keyboard()
        )
        await callback.answer()
        return

    # 2. Xabar matnini tayyorlash
    status_icon = "🟢" if summary["balance"] >= 0 else "🔴"
    text = (
        f"<b>📊 {period_title} moliyaviy hisobot:</b>\n\n"
        f"💰 <b>Kirim:</b> +{summary['income']:,.2f} so'm\n"
        f"💸 <b>Chiqim:</b> -{summary['expense']:,.2f} so'm\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💵 <b>Sof qoldiq:</b> {summary['balance']:,.2f} so'm {status_icon}\n\n"
    )

    # 3. Xarajatlar taqsimoti
    expense_data = await get_expenses_by_period(callback.from_user.id, start_date, now, db_session)
    if expense_data:
        text += "<b>📁 Xarajatlar taqsimoti:</b>\n"
        total_exp = summary["expense"] if summary["expense"] > 0 else 1
        for cat_name, amount in expense_data:
            pct = (amount / total_exp) * 100
            text += f"• <b>{cat_name}:</b> {amount:,.0f} so'm (<i>{pct:.1f}%</i>)\n"

    # Avvalgi inline menyuni o'chiramiz
    await callback.message.delete()

    # 4. Agar xarajat bo'lsa grafik yuboramiz
    if expense_data:
        chart_buffer = generate_pie_chart(expense_data)
        photo = BufferedInputFile(chart_buffer.read(), filename="chart.png")
        await callback.message.answer_photo(photo=photo, caption=text, parse_mode="HTML")
    else:
        await callback.message.answer(text, parse_mode="HTML")

    # 5. Excel hisobotini yuboramiz
    excel_buffer = generate_excel_report(detailed_transactions, summary)
    document = BufferedInputFile(
        excel_buffer.read(),
        filename=f"hisobot_{filename_prefix}_{now.strftime('%Y%m%d')}.xlsx"
    )
    await callback.message.answer_document(
        document=document,
        caption=f"📁 <b>{period_title} to'liq Excel hisoboti</b>",
        parse_mode="HTML"
    )
    await callback.answer()