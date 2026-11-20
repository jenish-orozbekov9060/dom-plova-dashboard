import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Пульт Качества (Дом плова)", layout="wide")
st.title("Пульт Качества (Дом плова)")
st.caption("Период анализа: 19 октября — 15 ноября 2026 года")

file_path = "data.xlsx"

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

                # --- УМНАЯ ПЛАШКА С АКЦЕНТОМ НА ДНИ ---
                if not df_hours_clean.empty and not df_branches.empty:
                    branches_only = df_branches[df_branches['Филиал'] != 'Итого']
                    worst_branch = branches_only.loc[branches_only['Заказы с инцидентом'].idxmax(), 'Филиал']
                    
                    worst_data = df_hours_clean[df_hours_clean['Филиал'] == worst_branch]
                    
                    if not worst_data.empty:
                        top_hour = worst_data.groupby('Час')['Случаев'].sum().idxmax()
                        top_reason = worst_data.groupby('Причина')['Случаев'].sum().idxmax()
                        
                        # Находим, в скольких днях повторялась эта проблема в этот час
                        worst_case_info = worst_data[(worst_data['Час'] == top_hour) & (worst_data['Причина'] == top_reason)]
                        days_count = int(worst_case_info['Дат'].max()) if not worst_case_info.empty else 0
                        
                        st.error(f"🚨 **Главная точка боли:** {worst_branch} \n\n"
                                 f"📍 **Пиковый час:** {top_hour} \n\n"
                                 f"⚠️ **Самая частая причина:** {top_reason} \n\n"
                                 f"🗓️ **Системность:** Эта проблема повторялась в **{days_count} разных дня** (это не разовая случайность).")

                # --- ОТРИСОВКА ---
                st.divider()
                st.subheader("1. Инциденты по филиалам")
                col1, col2 = st.columns(2)
                with col1:
                    st.dataframe(df_branches, hide_index=True)
                with col2:
                    plot_cols = [c for c in ['Партн. отмены', 'Неверные', 'Бэдфуд'] if c in df_branches.columns]
                    if plot_cols:
                        fig_branch = px.bar(df_branches, x='Филиал', y=plot_cols, 
                                            title="Структура инцидентов", barmode='group',
                                            color_discrete_sequence=['#D64545', '#E6A700', '#2E9E4F'])
                        st.plotly_chart(fig_branch, use_container_width=True)

                st.divider()
                st.subheader("2. В какое время и почему происходят инциденты?")
                
                if not df_hours_clean.empty:
                    branches_in_hours = df_hours_clean['Филиал'].dropna().unique()
                    selected_branch = st.selectbox("Выберите точку для детального анализа:", branches_in_hours)
                    
                    filtered_hours = df_hours_clean[df_hours_clean['Филиал'] == selected_branch]
                    
                    if not filtered_hours.empty:
                        fig_reasons = px.bar(filtered_hours, x='Час', y='Случаев', color='Причина', 
                                             title=f"Причины по часам: {selected_branch}",
                                             labels={'Случаев': 'Количество'})
                        st.plotly_chart(fig_reasons, use_container_width=True)
                        
                        # Детальная таблица с выделением дней
                        st.markdown("---")
                        st.subheader("📋 Детальный список (с указанием частоты)")
                        st.info("Обратите внимание на колонку **«Повторов (дней)»**. Если там больше 1, значит проблема системная.")
                        
                        display_df = filtered_hours[['Час', 'Метрика', 'Причина', 'Случаев', 'Дат']].copy()
                        display_df.columns = ['Время', 'Тип инцидента', 'Причина', 'Всего случаев', 'Повторов (дней)']
                        
                        # Сортируем по количеству случаев, чтобы самое важное было сверху
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