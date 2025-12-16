import streamlit as st
from datetime import datetime, timedelta
import calendar
import pandas as pd
import json
import os
import locale

# Configurar locale para português
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'pt_BR')
    except:
        pass  # Se não conseguir, continua em inglês

st.set_page_config(page_title="Sistema de Agendamento de Produção", page_icon="📦", layout="wide")

HISTORY_FILE = "historico_pedidos.json"
PARTS_FILE = "cadastro_pecas.json"
BLOCKED_DAYS_FILE = "dias_bloqueados.json"

# Funções de persistência
def save_parts_to_file():
    with open(PARTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(st.session_state.parts, f, indent=4, ensure_ascii=False)

def load_parts_from_file():
    if os.path.exists(PARTS_FILE):
        try:
            with open(PARTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_blocked_days():
    blocked_dates = [d.strftime('%Y-%m-%d') for d in st.session_state.blocked_days]
    with open(BLOCKED_DAYS_FILE, 'w', encoding='utf-8') as f:
        json.dump(blocked_dates, f, indent=4)

def load_blocked_days():
    if os.path.exists(BLOCKED_DAYS_FILE):
        try:
            with open(BLOCKED_DAYS_FILE, 'r', encoding='utf-8') as f:
                blocked_dates = json.load(f)
            return [datetime.strptime(d, '%Y-%m-%d').date() for d in blocked_dates]
        except:
            return []
    return []

def save_to_file():
    data = {
        'config': {
            'workers': st.session_state.workers,
            'minutes_per_day': st.session_state.minutes_per_day,
            'efficiency': st.session_state.efficiency,
            'config_saved': st.session_state.config_saved
        },
        'orders': []
    }
    
    for order in st.session_state.orders:
        order_copy = order.copy()
        order_copy['start_date'] = order['start_date'].strftime('%Y-%m-%d')
        order_copy['end_date'] = order['end_date'].strftime('%Y-%m-%d')
        data['orders'].append(order_copy)
    
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_from_file():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except:
            return None
    return None

def is_working_day(date):
    if date.weekday() >= 5:
        return False
    if date.date() in st.session_state.blocked_days:
        return False
    return True

def calculate_next_available_date(custom_start=None):
    if custom_start:
        current_date = custom_start
    elif not st.session_state.orders:
        current_date = datetime.now()
    else:
        last_end_date = max(order['end_date'] for order in st.session_state.orders)
        current_date = last_end_date + timedelta(days=1)
    
    while not is_working_day(current_date):
        current_date += timedelta(days=1)
    
    return current_date

def recalculate_all_dates(start_date=None):
    if not st.session_state.orders or not st.session_state.config_saved:
        return
    
    effective_minutes = st.session_state.minutes_per_day * (st.session_state.efficiency / 100)
    
    if start_date is None:
        current_date = datetime.now()
    else:
        current_date = start_date
    
    while not is_working_day(current_date):
        current_date += timedelta(days=1)
    
    for order in st.session_state.orders:
        order['start_date'] = current_date
        
        end_date, days_needed = calculate_end_date(
            current_date,
            order['total_minutes'],
            st.session_state.workers,
            effective_minutes
        )
        
        order['end_date'] = end_date
        order['days_needed'] = days_needed
        
        current_date = end_date + timedelta(days=1)
        while not is_working_day(current_date):
            current_date += timedelta(days=1)

def create_month_calendar(month_date, orders):
    year = month_date.year
    month = month_date.month
    
    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdatescalendar(year, month)
    
    # Nomes dos meses em português
    meses_pt = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
        5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
        9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }
    month_name = f"{meses_pt[month]} de {year}"
    
    html = f'<div style="margin: 20px; padding: 15px; background: white; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">'
    html += f'<h3 style="text-align: center; margin-bottom: 15px;">{month_name}</h3>'
    html += '<table style="width: 100%; border-collapse: collapse;">'
    
    html += '<tr>'
    for day in ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb']:
        html += f'<th style="padding: 10px; background: #e0e0e0; border: 1px solid #ccc; font-weight: bold;">{day}</th>'
    html += '</tr>'
    
    for week in month_days:
        html += '<tr>'
        for current_date in week:
            if current_date.month != month:
                html += '<td style="padding: 15px; border: 1px solid #ccc; background: #f5f5f5;"></td>'
            else:
                day = current_date.day
                is_weekend = current_date.weekday() >= 5
                is_blocked = current_date in st.session_state.blocked_days
                
                is_start = False
                is_end = False
                has_production = False
                order_names = []
                
                for idx, order in enumerate(orders):
                    if order['start_date'].date() == current_date:
                        is_start = True
                        order_names.append(f"#{idx+1}")
                    if order['end_date'].date() == current_date:
                        is_end = True
                    if order['start_date'].date() <= current_date <= order['end_date'].date():
                        if is_working_day(datetime.combine(current_date, datetime.min.time())):
                            has_production = True
                
                if is_start:
                    bg_color = '#c8e6c9'
                    text = f'{day} 🟢'
                    if order_names:
                        text += f"<br><small>{','.join(order_names)}</small>"
                elif is_end:
                    bg_color = '#ffcdd2'
                    text = f'{day} 🔴'
                elif is_blocked:
                    bg_color = '#ffeb3b'
                    text = f'{day} 🚫'
                elif has_production and not is_weekend and not is_blocked:
                    bg_color = '#bbdefb'
                    text = str(day)
                elif is_weekend:
                    bg_color = '#e0e0e0'
                    text = str(day)
                else:
                    bg_color = 'white'
                    text = str(day)
                
                font_weight = 'bold' if (is_start or is_end) else 'normal'
                html += f'<td style="padding: 15px; border: 1px solid #ccc; background: {bg_color}; text-align: center; font-weight: {font_weight};">{text}</td>'
        html += '</tr>'
    
    html += '</table></div>'
    return html

# Inicializar session state
if 'initialized' not in st.session_state:
    st.session_state.parts = load_parts_from_file()
    st.session_state.blocked_days = load_blocked_days()
    st.session_state.orders = []
    st.session_state.config_saved = False
    st.session_state.workers = None
    st.session_state.minutes_per_day = None
    st.session_state.efficiency = None
    st.session_state.temp_items = []
    
    # Carregar dados salvos
    saved_data = load_from_file()
    if saved_data:
        st.session_state.workers = saved_data['config'].get('workers')
        st.session_state.minutes_per_day = saved_data['config'].get('minutes_per_day')
        st.session_state.efficiency = saved_data['config'].get('efficiency')
        st.session_state.config_saved = saved_data['config'].get('config_saved', False)
        
        for order in saved_data['orders']:
            order_copy = order.copy()
            order_copy['start_date'] = datetime.strptime(order['start_date'], '%Y-%m-%d')
            order_copy['end_date'] = datetime.strptime(order['end_date'], '%Y-%m-%d')
            if 'items' not in order_copy:
                order_copy['items'] = [{
                    'part_name': 'Item Genérico',
                    'part_ref': 'N/A',
                    'quantity': 1,
                    'time_per_unit': order_copy.get('total_minutes', 0),
                    'total_time': order_copy.get('total_minutes', 0),
                    'production_order': 'N/A'
                }]
            st.session_state.orders.append(order_copy)
    
    st.session_state.initialized = True

# Interface
col_logo, col_title = st.columns([1, 5])
with col_logo:
    st.markdown('<div style="text-align: center; padding: 10px; font-size: 60px;">📦</div>', unsafe_allow_html=True)
with col_title:
    st.markdown('''
        <div style="padding-top: 15px;">
            <h1 style="margin: 0; color: #1f77b4;">Sistema de Agendamento de Produção</h1>
            <p style="margin: 5px 0 0 0; color: #666; font-size: 16px;">Gestão Inteligente de Pedidos e Produção</p>
        </div>
    ''', unsafe_allow_html=True)

st.markdown("---")

st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] {gap: 8px; background-color: #f0f2f6; padding: 10px; border-radius: 10px;}
    .stTabs [data-baseweb="tab"] {height: 50px; background-color: white; border-radius: 8px; padding: 0 24px; font-weight: 500; border: 2px solid #e0e0e0; transition: all 0.3s;}
    .stTabs [data-baseweb="tab"]:hover {background-color: #e3f2fd; border-color: #2196f3; transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.1);}
    .stTabs [aria-selected="true"] {background-color: #1f77b4 !important; color: white !important; border-color: #1f77b4 !important; box-shadow: 0 4px 12px rgba(31,119,180,0.3);}
    </style>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏭 Pedidos", "⚙️ Configuração", "🔧 Peças", "📅 Dias Bloqueados", "📊 Relatórios"])

# ABA 1: PEDIDOS
with tab1:
    st.caption(f"📋 Pedidos: {len(st.session_state.orders)} | Peças: {len(st.session_state.parts)} | Bloqueados: {len(st.session_state.blocked_days)}")
    st.markdown("---")
    
    if not st.session_state.config_saved:
        st.warning("⚠️ Configure a capacidade de produção primeiro na aba '⚙️ Configuração'!")
    else:
        effective_minutes = st.session_state.minutes_per_day * (st.session_state.efficiency / 100)
        effective_capacity = st.session_state.workers * effective_minutes
        st.info(f"⚙️ **Capacidade:** {st.session_state.workers} trabalhadores × {st.session_state.minutes_per_day} min/dia × {st.session_state.efficiency}% = **{effective_capacity:.0f} min/dia efetivos**")
        st.markdown("---")
        
        # Cadastrar novo pedido
        st.header("📦 Cadastrar Novo Pedido")
        
        if not st.session_state.parts:
            st.warning("⚠️ Cadastre peças primeiro na aba '🔧 Peças'!")
        else:
            col_name, col_date = st.columns([2, 1])
            
            with col_name:
                order_name = st.text_input("📝 Nome do Pedido", placeholder="Ex: Pedido #123", key="order_name")
            
            with col_date:
                next_available = calculate_next_available_date()
                custom_start_date = st.date_input("📅 Data de Início", value=next_available.date(), key="start_date")
            
            st.subheader("Adicionar Itens ao Pedido")
            
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                selected_part_idx = st.selectbox(
                    "Selecione a Peça",
                    range(len(st.session_state.parts)),
                    format_func=lambda x: f"{st.session_state.parts[x]['name']} (Ref: {st.session_state.parts[x]['reference']})",
                    key="select_part"
                )
            
            with col2:
                quantity = st.number_input("Quantidade", min_value=1, value=1, key="quantity")
            
            with col3:
                st.write("")
                st.write("")
                if st.button("➕ Adicionar Item", key="add_item"):
                    part = st.session_state.parts[selected_part_idx]
                    item = {
                        'part_name': part['name'],
                        'part_ref': part['reference'],
                        'quantity': quantity,
                        'time_per_unit': part['time_minutes'],
                        'total_time': quantity * part['time_minutes'],
                        'production_order': part['production_order']
                    }
                    st.session_state.temp_items.append(item)
                    st.rerun()
            
            if st.session_state.temp_items:
                st.write("**Itens do Pedido:**")
                
                for idx, item in enumerate(st.session_state.temp_items):
                    col_a, col_b = st.columns([5, 1])
                    with col_a:
                        st.write(f"• {item['part_name']} (Ref: {item['part_ref']}) - Qtd: {item['quantity']} - {item['total_time']} min - OP: {item['production_order']}")
                    with col_b:
                        if st.button("🗑️", key=f"del_{idx}"):
                            st.session_state.temp_items.pop(idx)
                            st.rerun()
                
                total_minutes = sum(item['total_time'] for item in st.session_state.temp_items)
                st.info(f"⏱️ **Total do Pedido: {total_minutes} minutos ({total_minutes/60:.1f} horas)**")
                
                start_datetime = datetime.combine(custom_start_date, datetime.min.time())
                end_date, days_needed = calculate_end_date(
                    start_datetime,
                    total_minutes,
                    st.session_state.workers,
                    effective_minutes
                )
                
                st.info(f"📅 **Início: {start_datetime.strftime('%d/%m/%Y')} | Fim: {end_date.strftime('%d/%m/%Y')} | Dias úteis: {days_needed}**")
                
                if st.button("✅ Finalizar e Adicionar Pedido", type="primary", key="finalize_order"):
                    if not order_name:
                        st.error("❌ Insira o nome do pedido!")
                    else:
                        order = {
                            'id': len(st.session_state.orders) + 1,
                            'name': order_name,
                            'items': st.session_state.temp_items.copy(),
                            'total_minutes': total_minutes,
                            'start_date': start_datetime,
                            'end_date': end_date,
                            'days_needed': days_needed
                        }
                        
                        st.session_state.orders.append(order)
                        st.session_state.temp_items = []
                        save_to_file()
                        st.success(f"✅ Pedido '{order_name}' adicionado!")
                        st.rerun()
            
            st.markdown("---")
        
        # Pedidos cadastrados
        if st.session_state.orders:
            st.header("📋 Pedidos Cadastrados")
            
            # Reordenação
            if len(st.session_state.orders) > 1:
                st.subheader("🔄 Reordenar Prioridades")
                col1, col2, col3, col4 = st.columns([3, 1, 1, 2])
                
                with col1:
                    order_to_move = st.selectbox(
                        "Selecione o pedido:",
                        range(len(st.session_state.orders)),
                        format_func=lambda x: f"#{x+1}: {st.session_state.orders[x]['name']}",
                        key="order_to_move"
                    )
                
                with col2:
                    if order_to_move > 0:
                        if st.button("⬆️ Subir", key="move_up"):
                            st.session_state.orders[order_to_move], st.session_state.orders[order_to_move-1] = \
                                st.session_state.orders[order_to_move-1], st.session_state.orders[order_to_move]
                            first_start = st.session_state.orders[0]['start_date']
                            recalculate_all_dates(first_start)
                            save_to_file()
                            st.rerun()
                
                with col3:
                    if order_to_move < len(st.session_state.orders) - 1:
                        if st.button("⬇️ Descer", key="move_down"):
                            st.session_state.orders[order_to_move], st.session_state.orders[order_to_move+1] = \
                                st.session_state.orders[order_to_move+1], st.session_state.orders[order_to_move]
                            first_start = st.session_state.orders[0]['start_date']
                            recalculate_all_dates(first_start)
                            save_to_file()
                            st.rerun()
                
                with col4:
                    if st.button("🔄 Recalcular Datas", key="recalc"):
                        first_start = st.session_state.orders[0]['start_date']
                        recalculate_all_dates(first_start)
                        save_to_file()
                        st.success("✅ Recalculado!")
                        st.rerun()
            
            # Lista de pedidos
            for idx, order in enumerate(st.session_state.orders):
                with st.expander(f"#{idx+1} - {order['name']} | {order['start_date'].strftime('%d/%m/%Y')} a {order['end_date'].strftime('%d/%m/%Y')} ({order['days_needed']} dias)"):
                    if 'items' in order and order['items']:
                        for item in order['items']:
                            st.write(f"• {item['part_name']} (Ref: {item['part_ref']}) - Qtd: {item['quantity']} - {item['total_time']} min - OP: {item['production_order']}")
                    else:
                        st.write(f"• Pedido antigo - Total: {order['total_minutes']} minutos")
                    
                    st.write(f"**Total: {order['total_minutes']} minutos**")
                    
                    if st.button(f"🗑️ Remover Pedido", key=f"rem_{idx}"):
                        st.session_state.orders.pop(idx)
                        if st.session_state.orders:
                            first_start = st.session_state.orders[0]['start_date']
                            recalculate_all_dates(first_start)
                        save_to_file()
                        st.rerun()
            
            st.markdown("---")
            
            # Calendário
            st.header("📅 Calendário de Produção")
            
            col_leg1, col_leg2, col_leg3, col_leg4, col_leg5 = st.columns(5)
            with col_leg1:
                st.markdown("🟢 **Início**")
            with col_leg2:
                st.markdown("📦 **Produção**")
            with col_leg3:
                st.markdown("🔴 **Fim**")
            with col_leg4:
                st.markdown("🚫 **Bloqueado**")
            with col_leg5:
                st.markdown("⬜ **Weekend**")
            
            all_dates = [o['start_date'] for o in st.session_state.orders] + [o['end_date'] for o in st.session_state.orders]
            min_date = min(all_dates)
            max_date = max(all_dates)
            
            current = datetime(min_date.year, min_date.month, 1)
            end = datetime(max_date.year, max_date.month, 1)
            
            months = []
            while current <= end:
                months.append(current)
                if current.month == 12:
                    current = datetime(current.year + 1, 1, 1)
                else:
                    current = datetime(current.year, current.month + 1, 1)
            
            for month_date in months:
                st.markdown(create_month_calendar(month_date, st.session_state.orders), unsafe_allow_html=True)

# ABA 2: CONFIGURAÇÃO
with tab2:
    st.header("⚙️ Configuração da Capacidade de Produção")
    st.info("💡 Configure a capacidade de produção da sua fábrica.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        workers_input = st.number_input("👥 Trabalhadores", min_value=1, value=int(st.session_state.workers) if st.session_state.workers else 1, key="cfg_workers")
    with col2:
        minutes_input = st.number_input("⏱️ Min/Dia", min_value=0.1, value=float(st.session_state.minutes_per_day) if st.session_state.minutes_per_day else 480.0, step=0.1, format="%.1f", key="cfg_minutes")
    with col3:
        efficiency_input = st.number_input("📊 Eficiência (%)", min_value=1, max_value=100, value=int(st.session_state.efficiency) if st.session_state.efficiency else 100, key="cfg_efficiency")
    
    st.markdown("---")
    
    if workers_input and minutes_input and efficiency_input:
        effective_minutes = minutes_input * (efficiency_input / 100)
        nominal_capacity = workers_input * minutes_input
        effective_capacity = workers_input * effective_minutes
        
        st.subheader("📊 Capacidade Calculada")
        col_calc1, col_calc2, col_calc3 = st.columns(3)
        with col_calc1:
            st.metric("💪 Nominal", f"{nominal_capacity:.0f} min/dia")
        with col_calc2:
            st.metric("⚡ Efetiva", f"{effective_capacity:.0f} min/dia")
        with col_calc3:
            st.metric("📈 Por Trabalhador", f"{effective_minutes:.0f} min")
    
    st.markdown("---")
    
    if st.button("💾 Salvar Configuração", type="primary", key="save_cfg"):
        st.session_state.workers = workers_input
        st.session_state.minutes_per_day = minutes_input
        st.session_state.efficiency = efficiency_input
        st.session_state.config_saved = True
        save_to_file()
        st.success("✅ Configuração salva com sucesso!")

# ABA 3: PEÇAS
with tab3:
    st.header("🔧 Cadastro de Peças")
    st.subheader("Adicionar Nova Peça")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        part_name = st.text_input("Nome da Peça", key="part_name")
    with col2:
        part_ref = st.text_input("Referência", key="part_ref")
    with col3:
        part_time = st.number_input("Tempo (min)", min_value=0.1, value=60.0, step=0.1, format="%.1f", key="part_time")
    with col4:
        part_order = st.text_input("Ordem Produção", key="part_order")
    
    if st.button("➕ Adicionar Peça", type="primary", key="add_part"):
        if part_name and part_ref:
            st.session_state.parts.append({
                'name': part_name,
                'reference': part_ref,
                'time_minutes': part_time,
                'production_order': part_order
            })
            save_parts_to_file()
            st.success(f"✅ Peça '{part_name}' cadastrada!")
            st.rerun()
        else:
            st.error("❌ Preencha nome e referência!")
    
    st.markdown("---")
    
    if st.session_state.parts:
        st.subheader("Peças Cadastradas")
        df_parts = pd.DataFrame(st.session_state.parts)
        st.dataframe(df_parts, use_container_width=True, hide_index=True)

# ABA 4: DIAS BLOQUEADOS
with tab4:
    st.header("📅 Cadastro de Dias Bloqueados")
    st.info("💡 Dias bloqueados não serão considerados como dias úteis.")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        blocked_date = st.date_input("Selecione a data", key="blocked_date")
    with col2:
        st.write("")
        st.write("")
        if st.button("🚫 Bloquear Data", type="primary", key="block_date"):
            if blocked_date not in st.session_state.blocked_days:
                st.session_state.blocked_days.append(blocked_date)
                st.session_state.blocked_days.sort()
                save_blocked_days()
                st.success(f"✅ Data bloqueada!")
                st.rerun()
            else:
                st.warning("⚠️ Data já bloqueada!")
    
    st.markdown("---")
    
    if st.session_state.blocked_days:
        st.subheader("Dias Bloqueados")
        blocked_df = pd.DataFrame([{
            'Data': d.strftime('%d/%m/%Y'),
            'Dia': ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'][d.weekday()]
        } for d in sorted(st.session_state.blocked_days)])
        st.dataframe(blocked_df, use_container_width=True, hide_index=True)

# ABA 5: RELATÓRIOS
with tab5:
    st.header("📊 Relatórios e Exportações")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📥 Exportar Peças")
        if st.session_state.parts:
            df = pd.DataFrame(st.session_state.parts)
            csv = df.to_csv(index=False, encoding='utf-8')
            st.download_button("📥 Download Peças", csv, f"pecas_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
    
    with col2:
        st.subheader("📥 Exportar Pedidos")
        if st.session_state.orders:
            st.info(f"{len(st.session_state.orders)} pedidos cadastrados")

st.markdown("---")
st.markdown('<div style="text-align: center; color: gray;"><p>Sistema v6.0 🚀</p></div>', unsafe_allow_html=True)