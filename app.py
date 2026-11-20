import streamlit as st
import pandas as pd
import plotly.express as px

# ============================================================
# НАСТРОЙКИ СТРАНИЦЫ И СТИЛИ
# ============================================================
st.set_page_config(page_title="Пульт Качества (Дом плова)", layout="wide")

# Добавляем CSS для красивых карточек KPI
st.markdown("""
<style>
    .kpi-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        font-family: sans-serif;
        color: #333;
        margin-bottom: 20px;
    }
    .kpi-title { font-size: 18px; color: #666; margin-bottom: 10px; font-weight: bold; }
    .kpi-value { font-size: 42px; font-weight: bold; margin-bottom: 5px; }
    .kpi-count { font-size: 14px; color: #888; margin-bottom: 15px; }
    .kpi-target { font-size: 14px; color: #555; margin-bottom: 5px; }
    .kpi-deviation { font-size: 14px; font-weight: bold; margin-bottom: 15px; }
    .kpi-details { font-size: 13px; color: #444; background: #f8f9fa; padding: 10px; border-radius: 5px; text-align: left;}
    .val-good { color: #2E9E4F; } /* Зеленый */
    .val-bad { color: #D64545; }  /* Красный */
</style>
""", unsafe_allow_html=True)

st.title("Пульт Качества (Дом плова)")
st.caption("Период анализа: 19 октября — 15 ноября 2026 года")

file_path = "data.xlsx"

# ВНИМАНИЕ: Для расчета процентов нужен общий пул заказов. 
# Если в вашем Excel есть общее кол-во заказов, подставьте его переменную сюда. 
# Сейчас здесь цифра (примерно 360 625), чтобы проценты совпадали с вашим скриншотом.
TOTAL_ORDERS = 360625 

try:
    raw_df = pd.read_excel(file_path, sheet_name="Сводная", header=None)

    # ============================================================
    # 1. ПОИСК ТАБЛИЦЫ ФИЛИАЛОВ
    # ============================================================
    start_row = None
    for i, row in raw_df.iterrows():
        if str(row[0]).strip() == "Итого":
            start_row = i
            break
            
    if start_row is not None:
        header_row = start_row - 1
        df_branches = raw_df.iloc[start_row : start_row + 4].copy()
        df_branches.columns = raw_df.iloc[header_row].values
        
        cols_to_keep = ['Филиал', 'Все отмены', 'Партн. отмены', 'Неверные', 'Бэдфуд', 'Заказы с инцидентом']
        available_cols = [c for c in cols_to_keep if c in df_branches.columns]
        df_branches = df_branches[available_cols].dropna(subset=['Филиал'])

        for col in cols_to_keep[1:]:
            if col in df_branches.columns:
                df_branches[col] = pd.to_numeric(df_branches[col], errors='coerce').fillna(0)

        # ============================================================
        # 1.5. БЛОК KPI (ТАРГЕТЫ И НАГЛЯДНОСТЬ)
        # ============================================================
        total_row = df_branches[df_branches['Филиал'] == 'Итого'].iloc[0] if 'Итого' in df_branches['Филиал'].values else None
        branches_only = df_branches[df_branches['Филиал'] != 'Итого']
        
        if total_row is not None:
            col1, col2, col3 = st.columns(3)
            
            # --- БЛОК 1: ОТМЕНЫ ---
            with col1:
                cancellations_count = total_row.get('Все отмены', 0)
                cancellations_pct = (cancellations_count / TOTAL_ORDERS) * 100
                target_cancel = 0.80
                dev_cancel = cancellations_pct - target_cancel
                
                color_class = "val-good" if cancellations_pct <= target_cancel else "val-bad"
                dev_color = "val-good" if dev_cancel <= 0 else "val-bad"
                dev_sign = "+" if dev_cancel > 0 else ""
                
                top2_cancel = branches_only.nlargest(2, 'Все отмены')[['Филиал', 'Все отмены']]
                top2_html = "<br>".join([f"{row['Филиал']}: {row['Все отмены']:,.0f} шт." for _, row in top2_cancel.iterrows()])
                
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title">Отмены</div>
                    <div class="kpi-value {color_class}">{cancellations_pct:.2f}%</div>
                    <div class="kpi-count">{cancellations_count:,.0f} шт.</div>
                    <hr style="margin: 10px 0; border-top: 1px solid #eee;">
                    <div class="kpi-target">Цель: {target_cancel:.2f}%</div>
                    <div class="kpi-deviation {dev_color}">Отклонение: {dev_sign}{dev_cancel:.2f}%</div>
                    <div class="kpi-details"><b>Худшие точки:</b><br>{top2_html}</div>
                </div>
                """, unsafe_allow_html=True)

            # --- БЛОК 2: ВРОНГИ (Неверные) ---
            with col2:
                wrong_count = total_row.get('Неверные', 0)
                wrong_pct = (wrong_count / TOTAL_ORDERS) * 100
                target_wrong = 0.60
                dev_wrong = wrong_pct - target_wrong
                
                color_class = "val-good" if wrong_pct <= target_wrong else "val-bad"
                dev_color = "val-good" if dev_wrong <= 0 else "val-bad"
                dev_sign = "+" if dev_wrong > 0 else ""
                
                top2_wrong = branches_only.nlargest(2, 'Неверные')[['Филиал', 'Неверные']]
                top2_html = "<br>".join([f"{row['Филиал']}: {row['Неверные']:,.0f} шт." for _, row in top2_wrong.iterrows()])
                
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title">Вронги (Неверные)</div>
                    <div class="kpi-value {color_class}">{wrong_pct:.2f}%</div>
                    <div class="kpi-count">{wrong_count:,.0f} шт.</div>
                    <hr style="margin: 10px 0; border-top: 1px solid #eee;">
                    <div class="kpi-target">Цель: {target_wrong:.2f}%</div>
                    <div class="kpi-deviation {dev_color}">Отклонение: {dev_sign}{dev_wrong:.2f}%</div>
                    <div class="kpi-details"><b>Худшие точки:</b><br>{top2_html}</div>
                </div>
                """, unsafe_allow_html=True)

            # --- БЛОК 3: БФ (Бэдфуд) ---
            with col3:
                bf_count = total_row.get('Бэдфуд', 0)
                bf_pct = (bf_count / TOTAL_ORDERS) * 100
                target_bf = 0.30
                dev_bf = bf_pct - target_bf
                
                color_class = "val-good" if bf_pct <= target_bf else "val-bad"
                dev_color = "val-good" if dev_bf <= 0 else "val-bad"
                dev_sign = "+" if dev_bf > 0 else ""
                
                top2_bf = branches_only.nlargest(2, 'Бэдфуд')[['Филиал', 'Бэдфуд']]
                top2_html = "<br>".join([f"{row['Филиал']}: {row['Бэдфуд']:,.0f} шт." for _, row in top2_bf.iterrows()])
                
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title">БФ (Бэдфуд)</div>
                    <div class="kpi-value {color_class}">{bf_pct:.2f}%</div>
                    <div class="kpi-count">{bf_count:,.0f} шт.</div>
                    <hr style="margin: 10px 0; border-top: 1px solid #eee;">
                    <div class="kpi-target">Цель: {target_bf:.2f}%</div>
                    <div class="kpi-deviation {dev_color}">Отклонение: {dev_sign}{dev_bf:.2f}%</div>
                    <div class="kpi-details"><b>Худшие точки:</b><br>{top2_html}</div>
                </div>
                """, unsafe_allow_html=True)

        # ============================================================
        # 2. ПОИСК ТАБЛИЦЫ ПО ЧАСАМ
        # ============================================================
        try:
            hour_header_idx = None
            for i, row in raw_df.iterrows():
                if 'Час' in row.values and 'Причина' in row.values:
                    hour_header_idx = i
                    break

            if hour_header_idx is not None:
                df_hours = raw_df.iloc[hour_header_idx + 1:].copy()
                df_hours.columns = raw_df.iloc[hour_header_idx].values
                
                cols_to_keep_h = ['Филиал', 'Час', 'Метрика', 'Причина', 'Случаев', 'Дат']
                available_cols_h = [c for c in cols_to_keep_h if c in df_hours.columns]
                df_hours = df_hours[available_cols_h].dropna(subset=['Час', 'Причина', 'Случаев'])
                
                df_hours['Случаев'] = pd.to_numeric(df_hours['Случаев'], errors='coerce').fillna(0)
                df_hours['Дат'] = pd.to_numeric(df_hours['Дат'], errors='coerce').fillna(0)

                df_hours_clean = df_hours[
                    (~df_hours['Час'].astype(str).str.contains('Все', case=False, na=False)) &
                    (~df_hours['Причина'].astype(str).str.contains('Все', case=False, na=False)) &
                    (df_hours['Час'].astype(str).str.contains(':', na=False))
                ]

                # --- УМНАЯ ПЛАШКА С АКЦЕНТОМ НА ДНИ (Оставляем) ---
                if not df_hours_clean.empty and not branches_only.empty:
                    worst_branch = branches_only.loc[branches_only['Заказы с инцидентом'].idxmax(), 'Филиал']
                    worst_data = df_hours_clean[df_hours_clean['Филиал'] == worst_branch]
                    
                    if not worst_data.empty:
                        top_hour = worst_data.groupby('Час')['Случаев'].sum().idxmax()
                        top_reason = worst_data.groupby('Причина')['Случаев'].sum().idxmax()
                        
                        worst_case_info = worst_data[(worst_data['Час'] == top_hour) & (worst_data['Причина'] == top_reason)]
                        days_count = int(worst_case_info['Дат'].max()) if not worst_case_info.empty else 0
                        
                        st.error(f"🚨 **Главная точка боли:** {worst_branch} \n\n"
                                 f"📍 **Пиковый час:** {top_hour} \n\n"
                                 f"⚠️ **Самая частая причина:** {top_reason} \n\n"
                                 f"🗓️ **Системность:** Эта проблема повторялась в **{days_count} разных дня** (это не разовая случайность).")

                # --- ОТРИСОВКА ТАБЛИЦЫ И ГРАФИКА ФИЛИАЛОВ ---
                st.divider()
                st.subheader("1. Общая картина по филиалам")
                col1, col2 = st.columns(2)
                with col1:
                    st.dataframe(df_branches, hide_index=True, use_container_width=True)
                with col2:
                    plot_cols = [c for c in ['Партн. отмены', 'Неверные', 'Бэдфуд'] if c in df_branches.columns]
                    if plot_cols:
                        fig_branch = px.bar(df_branches, x='Филиал', y=plot_cols, 
                                            title="Структура инцидентов", barmode='group',
                                            color_discrete_sequence=['#D64545', '#E6A700', '#2E9E4F'])
                        st.plotly_chart(fig_branch, use_container_width=True)

                st.divider()
                st.subheader("2. Детальный разбор инцидентов по часам")
                
                if not df_hours_clean.empty:
                    branches_in_hours = df_hours_clean['Филиал'].dropna().unique()
                    selected_branch = st.selectbox("Выберите точку для анализа:", branches_in_hours)
                    
                    filtered_hours = df_hours_clean[df_hours_clean['Филиал'] == selected_branch]
                    
                    if not filtered_hours.empty:
                        # --- БЛОК 2.1: ЧТО ПРОИСХОДИТ (ТОП ПРИЧИН) ---
                        st.markdown(f"#### 🔍 Главные проблемы: {selected_branch}")
                        
                        reasons_df = filtered_hours.groupby('Причина')['Случаев'].sum().reset_index()
                        reasons_df = reasons_df.sort_values(by='Случаев', ascending=True)
                        
                        top_reason = reasons_df.iloc[-1]['Причина']
                        top_reason_count = reasons_df.iloc[-1]['Случаев']
                        
                        fig_reasons = px.bar(
                            reasons_df, 
                            x='Случаев', 
                            y='Причина', 
                            orientation='h',
                            text='Случаев',
                            color_discrete_sequence=['#D64545'],
                            title="Рейтинг причин (от частых к редким)"
                        )
                        fig_reasons.update_traces(textposition='outside')
                        fig_reasons.update_layout(xaxis_title="Количество случаев", yaxis_title="", margin=dict(l=0, r=0, t=30, b=0))
                        st.plotly_chart(fig_reasons, use_container_width=True)

                        st.markdown("---")
                        
                        # --- БЛОК 2.2: КОГДА ПРОИСХОДИТ (ПИКОВЫЕ ЧАСЫ) ---
                        st.markdown(f"#### ⏰ В какое время происходят инциденты?")
                        
                        hours_df = filtered_hours.groupby('Час')['Случаев'].sum().reset_index()
                        hours_df = hours_df.sort_values(by='Случаев', ascending=False)
                        
                        worst_hour = hours_df.iloc[0]['Час']
                        
                        fig_hours = px.bar(
                            hours_df, 
                            x='Час', 
                            y='Случаев',
                            text='Случаев',
                            title="Нагрузка по инцидентам в течение дня"
                        )
                        
                        colors = ['#D64545' if hour == worst_hour else '#4C78A8' for hour in hours_df['Час']]
                        fig_hours.update_traces(marker_color=colors, textposition='outside')
                        fig_hours.update_layout(xaxis_title="Время", yaxis_title="Количество инцидентов", margin=dict(l=0, r=0, t=30, b=0))
                        
                        st.plotly_chart(fig_hours, use_container_width=True)

                        # --- БЛОК 2.3: ТЕКСТОВЫЙ ИНСАЙТ ---
                        st.info(f"""
                        💡 **Краткий вывод для управления точкой:**
                        *   Самая частая проблема — **«{top_reason}»** (всего {int(top_reason_count)} случаев).
                        *   Больше всего инцидентов происходит в период **{worst_hour}**.
                        *   **Рекомендация:** Усилить контроль на кухне/сборке именно в это время и обратить особое внимание на причину «{top_reason}».
                        """)

                        # --- БЛОК 2.4: ДЕТАЛЬНАЯ ТАБЛИЦА ---
                        st.markdown("---")
                        st.subheader("📋 Детальный список (с указанием частоты)")
                        
                        display_df = filtered_hours[['Час', 'Метрика', 'Причина', 'Случаев', 'Дат']].copy()
                        display_df.columns = ['Время', 'Тип инцидента', 'Причина', 'Всего случаев', 'Повторов (дней)']
                        display_df = display_df.sort_values(by='Всего случаев', ascending=False)
                        
                        st.dataframe(display_df, hide_index=True, use_container_width=True)
                    else:
                        st.warning("Нет детальных данных.")
                else:
                    st.warning("Нет данных по часам.")
            else:
                st.error("Таблица по часам не найдена в файле.")
                
        except Exception as e:
            st.error(f"Ошибка при чтении таблицы часов: {e}")

except Exception as e:
    st.error(f"Ошибка при чтении файла: {e}")
