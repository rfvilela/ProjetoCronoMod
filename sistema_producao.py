import streamlit as st
from datetime import datetime, timedelta
import calendar
import pandas as pd
import json
import os

# Configuração da página
st.set_page_config(
    page_title="Sistema de Agendamento de Produção",
    page_icon="📦",
    layout="wide"
)

# Nomes dos arquivos
HISTORY_FILE = "historico_pedidos.json"
PARTS_FILE = "cadastro_pecas.json"
BLOCKED_DAYS_FILE = "dias_bloqueados.json"

def save_blocked_days():
    """Salva dias bloqueados em arquivo JSON"""
    blocked_dates = [d.strftime('%Y-%m-%d') for d in st.session_state.blocked_days]
    with open(BLOCKED_DAYS_FILE, 'w', encoding='utf-8') as f:
        json.dump(blocked_dates, f, indent=4)

def load_blocked_days():
    """Carrega dias bloqueados do arquivo JSON"""
    if os.path.exists(BLOCKED_DAYS_FILE):
        try:
            with open(BLOCKED_DAYS_FILE, 'r', encoding='utf-8') as f:
                blocked_dates = json.load(f)
            st.session_state.blocked_days = [datetime.strptime(d, '%Y-%m-%d').date() for d in blocked_dates]
            return True
        except Exception as e:
            st.error(f"❌ Erro ao carregar dias bloqueados: {str(e)}")
            return False
    return False

def is_working_day(date):
    """Verifica se é um dia útil (não é fim de semana nem está bloqueado)"""
    if date.weekday() >= 5:  # Sábado ou Domingo
        return False
    if date.date() in st.session_state.blocked_days:
        return False
    return True

def save_parts_to_file():
    """Salva cadastro de peças em arquivo JSON"""
    with open(PARTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(st.session_state.parts, f, indent=4, ensure_ascii=False)

def load_parts_from_file():
    """Carrega cadastro de peças do arquivo JSON"""
    if os.path.exists(PARTS_FILE):
        try:
            with open(PARTS_FILE, 'r', encoding='utf-8') as f:
                st.session_state.parts = json.load(f)
            return True
        except Exception as e:
            st.error(f"❌ Erro ao carregar peças: {str(e)}")
            return False
    return False

def save_to_file():
    """Salva todos os dados em arquivo JSON"""
    data = {
        'config': {
            'workers': st.session_state.workers,
            'minutes_per_day': st.session_state.minutes_per_day,
            'efficiency': st.session_state.efficiency,
            'config_saved': st.session_state.config_saved
        },
        'orders': []
    }
    
    # Converter datas para string para salvar em JSON
    for order in st.session_state.orders:
        order_copy = order.copy()
        order_copy['start_date'] = order['start_date'].strftime('%Y-%m-%d')
        order_copy['end_date'] = order['end_date'].strftime('%Y-%m-%d')
        data['orders'].append(order_copy)
    
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_from_file():
    """Carrega dados do arquivo JSON"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Carregar configuração
            st.session_state.workers = data['config'].get('workers')
            st.session_state.minutes_per_day = data['config'].get('minutes_per_day')
            st.session_state.efficiency = data['config'].get('efficiency')
            st.session_state.config_saved = data['config'].get('config_saved', False)
            
            # Carregar pedidos
            st.session_state.orders = []
            for order in data['orders']:
                order_copy = order.copy()
                order_copy['start_date'] = datetime.strptime(order['start_date'], '%Y-%m-%d')
                order_copy['end_date'] = datetime.strptime(order['end_date'], '%Y-%m-%d')
                
                # Compatibilidade: se não tem 'items', cria um item genérico
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
            
            return True
        except Exception as e:
            st.error(f"❌ Erro ao carregar histórico: {str(e)}")
            return False
    return False

def export_orders_to_csv():
    """Exporta pedidos para CSV"""
    if st.session_state.orders:
        rows = []
        for idx, o in enumerate(st.session_state.orders):
            # Verifica se tem items (novo formato)
            if 'items' in o and o['items']:
                for item in o['items']:
                    rows.append({
                        'Prioridade': idx + 1,
                        'Pedido': o['name'],
                        'Peça': item['part_name'],
                        'Referencia': item['part_ref'],
                        'Quantidade': item['quantity'],
                        'Min_Unitario': item['time_per_unit'],
                        'Min_Total': item['total_time'],
                        'Ordem_Producao': item['production_order'],
                        'Data_Inicio': o['start_date'].strftime('%d/%m/%Y'),
                        'Data_Fim': o['end_date'].strftime('%d/%m/%Y'),
                        'Dias_Uteis': o['days_needed']
                    })
            else:
                # Pedido antigo sem items
                rows.append({
                    'Prioridade': idx + 1,
                    'Pedido': o['name'],
                    'Peça': 'N/A',
                    'Referencia': 'N/A',
                    'Quantidade': 'N/A',
                    'Min_Unitario': 'N/A',
                    'Min_Total': o['total_minutes'],
                    'Ordem_Producao': 'N/A',
                    'Data_Inicio': o['start_date'].strftime('%d/%m/%Y'),
                    'Data_Fim': o['end_date'].strftime('%d/%m/%Y'),
                    'Dias_Uteis': o['days_needed']
                })
        
        df = pd.DataFrame(rows)
        return df.to_csv(index=False, encoding='utf-8')
    return None

def export_parts_to_csv():
    """Exporta peças para CSV"""
    if st.session_state.parts:
        df = pd.DataFrame(st.session_state.parts)
        return df.to_csv(index=False, encoding='utf-8')
    return None

def recalculate_all_dates(start_date=None):
    """Recalcula todas as datas dos pedidos baseado na ordem atual"""
    if not st.session_state.orders or not st.session_state.config_saved:
        return
    
    effective_minutes = st.session_state.minutes_per_day * (st.session_state.efficiency / 100)
    
    if start_date is None:
        current_date = datetime.now()
    else:
        current_date = start_date
    
    # Avançar para o próximo dia útil
    while not is_working_day(current_date):
        current_date += timedelta(days=1)
    
    for order in st.session_state.orders:
        # Definir data de início
        order['start_date'] = current_date
        
        # Calcular data de término
        end_date, days_needed = calculate_end_date(
            current_date,
            order['total_minutes'],
            st.session_state.workers,
            effective_minutes
        )
        
        order['end_date'] = end_date
        order['days_needed'] = days_needed
        
        # Próximo pedido começa no dia útil seguinte
        current_date = end_date + timedelta(days=1)
        while not is_working_day(current_date):
            current_date += timedelta(days=1)

# Inicializar session_state
if 'blocked_days' not in st.session_state:
    st.session_state.blocked_days = []
    load_blocked_days()

if 'parts' not in st.session_state:
    st.session_state.parts = []
    load_parts_from_file()

if 'orders' not in st.session_state:
    st.session_state.orders = []
if 'config_saved' not in st.session_state:
    st.session_state.config_saved = False
if 'workers' not in st.session_state:
    st.session_state.workers = None
if 'minutes_per_day' not in st.session_state:
    st.session_state.minutes_per_day = None
if 'efficiency' not in st.session_state:
    st.session_state.efficiency = None
if 'loaded' not in st.session_state:
    st.session_state.loaded = False
    load_from_file()

def calculate_next_available_date(custom_start=None):
    """Calcula a próxima data disponível baseada nos pedidos existentes"""
    if custom_start:
        # Se há uma data customizada, usa ela
        current_date = custom_start
    elif not st.session_state.orders:
        # Se não há pedidos, começa hoje
        current_date = datetime.now()
    else:
        # Pega a última data de término
        last_end_date = max(order['end_date'] for order in st.session_state.orders)
        current_date = last_end_date + timedelta(days=1)
    
    # Avançar para o próximo dia útil
    while not is_working_day(current_date):
        current_date += timedelta(days=1)
    
    return current_date

def calculate_end_date(start_date, total_minutes, workers, effective_minutes):
    """Calcula a data de término baseado na capacidade efetiva"""
    daily_capacity = workers * effective_minutes
    days_needed = int((total_minutes + daily_capacity - 1) // daily_capacity)
    
    current_date = start_date
    work_days = 0
    
    while work_days < days_needed:
        current_date += timedelta(days=1)
        if is_working_day(current_date):
            work_days += 1
    
    return current_date, days_needed

def create_month_calendar(month_date, orders):
    """Cria um calendário mensal em HTML"""
    year = month_date.year
    month = month_date.month
    
    # Usar calendar.Calendar para obter o mês com semanas completas
    cal = calendar.Calendar(firstweekday=6)  # Começa no domingo
    month_days = cal.monthdatescalendar(year, month)
    
    month_name = month_date.strftime('%B de %Y').capitalize()
    
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
            # Se o dia não pertence ao mês atual, deixa vazio
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

# Título principal
st.title("📦 Sistema de Agendamento de Produção")

# Abas principais
tab1, tab2, tab3, tab4 = st.tabs(["🏭 Produção", "🔧 Cadastro de Peças", "📅 Dias Bloqueados", "📊 Relatórios"])

# ===== ABA 1: PRODUÇÃO =====
with tab1:
    # Barra de informações
    col_info1, col_info2, col_info3 = st.columns([2, 2, 1])
    with col_info1:
        if os.path.exists(HISTORY_FILE):
            file_time = datetime.fromtimestamp(os.path.getmtime(HISTORY_FILE))
            st.caption(f"💾 Último salvamento: {file_time.strftime('%d/%m/%Y %H:%M:%S')}")
        else:
            st.caption("💾 Nenhum histórico salvo ainda")
    
    with col_info2:
        st.caption(f"📋 Pedidos: {len(st.session_state.orders)} | Peças: {len(st.session_state.parts)} | Bloqueados: {len(st.session_state.blocked_days)}")
    
    with col_info3:
        if st.button("🔄 Recarregar"):
            load_from_file()
            load_parts_from_file()
            load_blocked_days()
            st.success("✅ Dados recarregados!")
            st.rerun()
    
    st.markdown("---")
    
    # Configuração
    st.header("⚙️ Configuração da Capacidade de Produção")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        workers_input = st.number_input(
            "👥 Trabalhadores",
            min_value=1,
            value=st.session_state.workers if st.session_state.workers else 1,
            disabled=st.session_state.config_saved
        )
    
    with col2:
        minutes_input = st.number_input(
            "⏱️ Min/Dia (por trabalhador)",
            min_value=1,
            value=st.session_state.minutes_per_day if st.session_state.minutes_per_day else 480,
            disabled=st.session_state.config_saved
        )
    
    with col3:
        efficiency_input = st.number_input(
            "📊 Eficiência (%)",
            min_value=1,
            max_value=100,
            value=st.session_state.efficiency if st.session_state.efficiency else 100,
            disabled=st.session_state.config_saved
        )
    
    if not st.session_state.config_saved:
        if st.button("💾 Salvar Configuração", type="primary"):
            st.session_state.workers = workers_input
            st.session_state.minutes_per_day = minutes_input
            st.session_state.efficiency = efficiency_input
            st.session_state.config_saved = True
            save_to_file()
            st.rerun()
    else:
        effective_minutes = st.session_state.minutes_per_day * (st.session_state.efficiency / 100)
        effective_capacity = st.session_state.workers * effective_minutes
        
        st.success(f"✅ Capacidade: {effective_capacity:.0f} min/dia efetivos ({effective_capacity/60:.1f}h/dia)")
        
        if st.button("✏️ Editar Configuração"):
            st.session_state.config_saved = False
            st.rerun()
    
    st.markdown("---")
    
    # Cadastro de Pedidos
    if st.session_state.config_saved:
        st.header("📦 Cadastrar Novo Pedido")
        
        if not st.session_state.parts:
            st.warning("⚠️ Cadastre peças primeiro na aba 'Cadastro de Peças'!")
        else:
            col_name, col_date = st.columns([2, 1])
            
            with col_name:
                order_name = st.text_input("📝 Nome do Pedido", placeholder="Ex: Pedido #123")
            
            with col_date:
                # Campo para definir data de início personalizada
                custom_start_date = st.date_input(
                    "📅 Data de Início",
                    value=calculate_next_available_date().date(),
                    help="Defina a data de início deste pedido"
                )
            
            st.subheader("Adicionar Itens ao Pedido")
            
            # Usar session_state para armazenar itens temporários
            if 'temp_items' not in st.session_state:
                st.session_state.temp_items = []
            
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                selected_part_idx = st.selectbox(
                    "Selecione a Peça",
                    range(len(st.session_state.parts)),
                    format_func=lambda x: f"{st.session_state.parts[x]['name']} (Ref: {st.session_state.parts[x]['reference']})"
                )
            
            with col2:
                quantity = st.number_input("Quantidade", min_value=1, value=1)
            
            with col3:
                st.write("")
                st.write("")
                if st.button("➕ Adicionar Item"):
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
            
            # Mostrar itens adicionados
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
                
                # Calcular data de término baseado na data customizada
                start_datetime = datetime.combine(custom_start_date, datetime.min.time())
                effective_minutes = st.session_state.minutes_per_day * (st.session_state.efficiency / 100)
                end_date, days_needed = calculate_end_date(
                    start_datetime,
                    total_minutes,
                    st.session_state.workers,
                    effective_minutes
                )
                
                st.info(f"📅 **Início: {start_datetime.strftime('%d/%m/%Y')} | Fim: {end_date.strftime('%d/%m/%Y')} | Dias úteis: {days_needed}**")
                
                if st.button("✅ Finalizar e Adicionar Pedido", type="primary"):
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
        
        # Pedidos Cadastrados
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
                        format_func=lambda x: f"#{x+1}: {st.session_state.orders[x]['name']}"
                    )
                
                with col2:
                    if order_to_move > 0:
                        if st.button("⬆️ Subir"):
                            st.session_state.orders[order_to_move], st.session_state.orders[order_to_move-1] = \
                                st.session_state.orders[order_to_move-1], st.session_state.orders[order_to_move]
                            # Manter a data de início do primeiro pedido
                            first_start = st.session_state.orders[0]['start_date']
                            recalculate_all_dates(first_start)
                            save_to_file()
                            st.rerun()
                
                with col3:
                    if order_to_move < len(st.session_state.orders) - 1:
                        if st.button("⬇️ Descer"):
                            st.session_state.orders[order_to_move], st.session_state.orders[order_to_move+1] = \
                                st.session_state.orders[order_to_move+1], st.session_state.orders[order_to_move]
                            # Manter a data de início do primeiro pedido
                            first_start = st.session_state.orders[0]['start_date']
                            recalculate_all_dates(first_start)
                            save_to_file()
                            st.rerun()
                
                with col4:
                    if st.button("🔄 Recalcular Todas as Datas"):
                        # Manter a data de início do primeiro pedido
                        first_start = st.session_state.orders[0]['start_date']
                        recalculate_all_dates(first_start)
                        save_to_file()
                        st.success("✅ Datas recalculadas!")
                        st.rerun()
            
            # Lista de pedidos
            for idx, order in enumerate(st.session_state.orders):
                with st.expander(f"#{idx+1} - {order['name']} | {order['start_date'].strftime('%d/%m/%Y')} a {order['end_date'].strftime('%d/%m/%Y')} ({order['days_needed']} dias)"):
                    # Verifica se tem items (novo formato) ou exibe dados antigos
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
            st.header("📅 Calendário")
            
            # Legenda
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

# ===== ABA 2: CADASTRO DE PEÇAS =====
with tab2:
    st.header("🔧 Cadastro de Peças")
    
    st.subheader("Adicionar Nova Peça")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        part_name = st.text_input("Nome da Peça", placeholder="Ex: Engrenagem")
    
    with col2:
        part_ref = st.text_input("Referência/Código", placeholder="Ex: ENG-001")
    
    with col3:
        part_time = st.number_input("Tempo (minutos)", min_value=1, value=60)
    
    with col4:
        part_order = st.text_input("Ordem de Produção", placeholder="Ex: OP-2024-001")
    
    if st.button("➕ Adicionar Peça", type="primary"):
        if not part_name or not part_ref:
            st.error("❌ Preencha nome e referência!")
        else:
            part = {
                'name': part_name,
                'reference': part_ref,
                'time_minutes': part_time