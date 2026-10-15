import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# Настройка страницы
st.set_page_config(
    page_title="Семейный Финансовый План (Кавальчук)",
    page_icon="🏡",
    layout="wide"
)

st.title("🏡 Семейный Финансовый План и Траектория Ипотеки (2026–2033)")
st.markdown(
    "**Семья:** Илья и Виктория Кавальчук | "
    "**Баланс Офсета (Окт 2026):** `$63,598.30` | "
    "**Цель:** Полное закрытие ипотеки к **Сентябрю 2031 г.**"
)

st.divider()

# --- БОКОВАЯ ПАНЕЛЬ (ПОЛЗУНКИ НАСТРОЙКИ) ---
st.sidebar.header("⚙️ Настройка параметров")

st.sidebar.subheader("1. Доходы семьи (чистыми в месяц)")
ilya_income = st.sidebar.number_input("Зарплата Ильи (Swinburne, $/мес)", value=8020, step=100)
vicky_income = st.sidebar.number_input("Зарплата Виктории (ECE, без няни, $/мес)", value=2080, step=100)
total_income = ilya_income + vicky_income

st.sidebar.subheader("2. Параметры Ипотеки и Офсета")
gross_loan = st.sidebar.slider("Общий остаток тела кредита ($)", 250000, 420000, 308600, step=1000)
current_offset = st.sidebar.number_input("Текущий баланс на Офсете ($)", value=63598, step=500)
interest_rate = st.sidebar.slider("Ставка по ипотеке (% годовых)", 4.0, 8.0, 6.43, step=0.05) / 100
vicky_fortnightly = st.sidebar.slider("Вклад Виктории в ипотеку ($ раз в 2 недели)", 0, 800, 500, step=50)
vicky_monthly_mortgage = vicky_fortnightly * 26 / 12

st.sidebar.subheader("3. Личные бюджеты и Хобби ($/мес)")
vicky_personal = st.sidebar.slider("Личный фонд Виктории (салоны, уход, $)", 200, 1000, 500, step=50)
ilya_personal = st.sidebar.slider("Личный фонд Ильи (LEGO, хобби, $)", 50, 500, 200, step=25)
karting_budget = st.sidebar.slider("Картинг и автоспорт ($)", 0, 500, 220, step=20)
groceries_budget = st.sidebar.slider("Продукты, рынки и быт ($)", 900, 1800, 1265, step=25)

# --- РАСЧЕТ ЕЖЕМЕСЯЧНОГО БЮДЖЕТА ---
fixed_home_bills = 845      # Council Rates ($243), AGL ($229), Telstra/Vodafone ($220), AAMI Дом ($78), Школа/Банк ($75)
mandatory_mortgage = 2517   # Обязательный платеж по кредиту ($1,161.60 раз в 2 недели)
transport_costs = 415       # Бензин ($180), Myki/Linkt ($135), AAMI Авто ($100)
garden_and_dining = 95 + 175 # Bunnings/Сад ($95) + Кафе и подписки ($175)

total_expenses = (
    mandatory_mortgage + fixed_home_bills + groceries_budget + 
    transport_costs + vicky_personal + ilya_personal + 
    karting_budget + garden_and_dining
)

monthly_offset_surplus_with_vicky = total_income - total_expenses
monthly_offset_surplus_without_vicky = monthly_offset_surplus_with_vicky - vicky_monthly_mortgage

# --- БЛОК 1: КЛЮЧЕВЫЕ ПОКАЗАТЕЛИ ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Общий доход семьи", f"${total_income:,.0f} / мес", "Базовый (без няни)")
col2.metric("Все расходы (вкл. ипотеку)", f"${total_expenses:,.0f} / мес", f"{total_expenses/total_income*100:.1f}% от дохода")
col3.metric("Прирост Офсета (С вкладом Виктории)", f"+${monthly_offset_surplus_with_vicky:,.0f} / мес", f"Вкл. ${vicky_monthly_mortgage:,.0f}/мес от Виктории")
col4.metric("Текущий чистый долг", f"${gross_loan - current_offset:,.0f}", f"Офсет: ${current_offset:,.0f}")

st.divider()

# --- СИМУЛЯЦИЯ ПОГАШЕНИЯ ---
months = 84
r_monthly = interest_rate / 12
dates = pd.date_range(start="2026-10-01", periods=months + 1, freq="MS")

net_debt_with = [gross_loan - current_offset]
net_debt_without = [gross_loan - current_offset]

total_cash_to_loan_with = mandatory_mortgage + monthly_offset_surplus_with_vicky
total_cash_to_loan_without = mandatory_mortgage + monthly_offset_surplus_without_vicky

payoff_date_with = "После 2033 г."
payoff_date_without = "После 2033 г."

for m in range(1, months + 1):
    prev_w = net_debt_with[-1]
    if prev_w > 0:
        interest_w = prev_w * r_monthly
        new_w = max(0.0, prev_w + interest_w - total_cash_to_loan_with)
        if new_w == 0 and payoff_date_with == "После 2033 г.":
            payoff_date_with = dates[m].strftime("%B %Y")
    else:
        new_w = 0.0
    net_debt_with.append(new_w)

    prev_wo = net_debt_without[-1]
    if prev_wo > 0:
        interest_wo = prev_wo * r_monthly
        new_wo = max(0.0, prev_wo + interest_wo - total_cash_to_loan_without)
        if new_wo == 0 and payoff_date_without == "После 2033 г.":
            payoff_date_without = dates[m].strftime("%B %Y")
    else:
        new_wo = 0.0
    net_debt_without.append(new_wo)

n_target = 59
direct_vicky_5yr = vicky_monthly_mortgage * n_target
fv_vicky_5yr = vicky_monthly_mortgage * (((1 + r_monthly) ** n_target - 1) / r_monthly)
interest_saved_vicky = fv_vicky_5yr - direct_vicky_5yr

# --- ГРАФИК И ТАБЛИЦА ---
left_col, right_col = st.columns([3, 2])

with left_col:
    st.subheader("📉 Траектория чистого долга: Сравнение сценариев")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=net_debt_with, mode='lines',
        name=f'С вкладом Виктории (${vicky_fortnightly}/2 нед.) — Закрытие: {payoff_date_with}',
        line=dict(color='#10b981', width=4)
    ))
    fig.add_trace(go.Scatter(
        x=dates, y=net_debt_without, mode='lines',
        name=f'Без вклада Виктории — Закрытие: {payoff_date_without}',
        line=dict(color='#ef4444', width=3, dash='dash')
    ))
    fig.update_layout(
        xaxis_title="Год",
        yaxis_title="Чистый остаток долга (Кредит минус Офсет, AUD)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

    st.success(
        f"💡 **Математика вклада Виктории за 5 лет (до сентября 2031 г.):**\n"
        f"- Прямые переводы (${vicky_fortnightly} раз в 2 нед.): **${direct_vicky_5yr:,.0f}**\n"
        f"- Сэкономленные проценты банку ANZ (под {interest_rate*100:.2f}% годовых): **+${interest_saved_vicky:,.0f}**\n"
        f"- **Общий вклад Виктории в закрытие ипотеки: ${fv_vicky_5yr:,.0f}** "
        f"(Дата полного закрытия: **{payoff_date_with}** вместо **{payoff_date_without}**)"
    )

with right_col:
    st.subheader("📊 Куда уходят деньги в месяц")
    budget_df = pd.DataFrame({
        "Категория": [
            "1. Обязательный платеж по ипотеке",
            "2. Счета за дом, налоги, страховка дома и школа",
            "3. Продукты, рынки и быт (Aldi, Coles, Food Factory)",
            "4. Транспорт, бензин, Myki и автостраховка",
            "5. Личный фонд Виктории (салоны, уход за собой)",
            "6. Картинг и автоспорт (GKCV, запчасти)",
            "7. Личный фонд Ильи (LEGO, хобби)",
            "8. Сад (Bunnings), кафе и подписки",
            "💰 ЧИСТЫЙ ПЛЮС В ОФСЕТ (Сверх платежа по ипотеке)"
        ],
        "Сумма ($/мес)": [
            mandatory_mortgage, fixed_home_bills, groceries_budget,
            transport_costs, vicky_personal, karting_budget,
            ilya_personal, garden_and_dining, monthly_offset_surplus_with_vicky
        ]
    })
    budget_df["Доля (%)"] = (budget_df["Сумма ($/мес)"] / total_income * 100).round(1).astype(str) + "%"
    st.dataframe(budget_df, use_container_width=True, hide_index=True)