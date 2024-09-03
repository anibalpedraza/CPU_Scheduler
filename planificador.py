import tkinter as tk
from tkinter import messagebox, ttk

# ======== Helpers globales para la tabla de ciclos ========
timeline_data = {}    # {pid: ['','X','O',...]}
arrival_marks = {}    # {pid: col_index_a_sombrear}
total_time = 0        # último ciclo
all_pids = []         # orden de filas en la tabla de ciclos

def init_timeline_from_process_table():
    """Inicializa estructuras para la tabla de ciclos a partir de la tabla de procesos."""
    global timeline_data, arrival_marks, total_time, all_pids
    timeline_data = {}
    arrival_marks = {}
    total_time = 0
    all_pids = []
    for child in process_table.get_children():
        pid = str(process_table.item(child)['values'][0])
        arr = int(process_table.item(child)['values'][1])
        all_pids.append(pid)
        timeline_data[pid] = []           # se rellenará ciclo a ciclo
        arrival_marks[pid] = arr + 1      # se sombreará esta columna (columna 1 == ciclo 1)

def _ensure_len(pid, t):
    """Asegura que la lista del proceso tenga longitud al menos t, rellenando con ''."""
    while len(timeline_data[pid]) < t:
        timeline_data[pid].append('')

def log_cycle(t, running_pid, queue_pids):
    """Marca, para el ciclo t (1..), quién corre (X) y quién espera (O)."""
    global total_time
    for pid in all_pids:
        _ensure_len(pid, t)
        if pid == running_pid:
            timeline_data[pid][t-1] = 'X'
        elif pid in queue_pids:
            # Sólo marcamos O si aún no está marcada X en ese ciclo.
            timeline_data[pid][t-1] = timeline_data[pid][t-1] or 'O'
        # else: vacío
    total_time = max(total_time, t)

def render_cycle_table():
    """Dibuja la rejilla de ciclos con sombreado en las llegadas."""
    # Limpiar si ya existe
    for w in cycle_container.winfo_children():
        w.destroy()

    if total_time == 0 or not all_pids:
        return

    # Scroll horizontal
    canvas = tk.Canvas(cycle_container, height=260)
    hscroll = tk.Scrollbar(cycle_container, orient='horizontal', command=canvas.xview)
    canvas.configure(xscrollcommand=hscroll.set)
    canvas.grid(row=0, column=0, sticky="nsew")
    hscroll.grid(row=1, column=0, sticky="ew")
    cycle_container.grid_rowconfigure(0, weight=1)
    cycle_container.grid_columnconfigure(0, weight=1)

    grid_frame = tk.Frame(canvas)
    canvas.create_window((0, 0), window=grid_frame, anchor="nw")

    # Estilos visuales
    cell_w = 28
    cell_h = 22
    bd = 1

    # Cabecera
    tk.Label(grid_frame, text="FCFS/SJF/SRTF/RR", width=14, anchor="w").grid(row=0, column=0, sticky="nsew")
    for c in range(1, total_time+1):
        tk.Label(grid_frame, text=str(c), width=int(cell_w/8), relief="raised")\
          .grid(row=0, column=c, sticky="nsew")

    # Filas por proceso
    for r, pid in enumerate(all_pids, start=1):
        tk.Label(grid_frame, text=pid, width=14, anchor="w", relief="groove")\
          .grid(row=r, column=0, sticky="nsew")
        row_vals = timeline_data.get(pid, [])
        for c in range(1, total_time+1):
            txt = row_vals[c-1] if c-1 < len(row_vals) else ''
            bg = "SystemButtonFace"
            # sombreado de llegada
            if arrival_marks.get(pid, -1) == c:
                bg = "#d9d9d9"
            tk.Label(grid_frame, text=txt, width=int(cell_w/8), height=1,
                     relief="groove", bd=bd, bg=bg)\
              .grid(row=r, column=c, sticky="nsew")

    # Ajuste del scrollregion
    grid_frame.update_idletasks()
    canvas.configure(scrollregion=canvas.bbox("all"))

# ======== Algoritmos ========

# Algoritmo First-Come, First-Served (FCFS)
def first_come_first_served():
    time = 0
    queue = []
    completed_list = []

    def add_to_queue():
        nonlocal queue
        for process in process_list[:]:
            if time >= process['arrivalTime']:
                queue.append(process)
                process_list.remove(process)

    init_timeline_from_process_table()
    add_to_queue()
    if not queue and not process_list:
        display_results([])
        return

    # Si está vacío, ocioso hasta que llegue algo
    while not queue and process_list:
        time += 1
        add_to_queue()
        log_cycle(time, None, [p['processID'] for p in queue])

    while process_list or queue:
        if not queue:
            time += 1
            add_to_queue()
            log_cycle(time, None, [p['processID'] for p in queue])
            continue

        process = queue.pop(0)
        for _ in range(process['durationTime']):
            time += 1
            add_to_queue()
            # === Ciclos ===
            log_cycle(time, process['processID'], [p['processID'] for p in queue])

        process['completedTime'] = time
        process['turnAroundTime'] = process['completedTime'] - process['arrivalTime']
        process['waitingTime'] = process['turnAroundTime'] - process['durationTime']
        completed_list.append(process)

    display_results(completed_list)
    render_cycle_table()

# Algoritmo Shortest Job First (SJF)
def shortest_job_first():
    time = 0
    queue = []
    completed_list = []

    def add_to_queue():
        nonlocal queue
        for process in process_list[:]:
            if time >= process['arrivalTime']:
                queue.append(process)
                process_list.remove(process)
        queue.sort(key=lambda x: x['durationTime'])

    init_timeline_from_process_table()
    add_to_queue()
    while not queue and process_list:
        time += 1
        add_to_queue()
        log_cycle(time, None, [p['processID'] for p in queue])

    while process_list or queue:
        if not queue:
            time += 1
            add_to_queue()
            log_cycle(time, None, [p['processID'] for p in queue])
            continue

        process = queue.pop(0)
        for _ in range(process['durationTime']):
            time += 1
            add_to_queue()
            log_cycle(time, process['processID'], [p['processID'] for p in queue])

        process['completedTime'] = time
        process['turnAroundTime'] = process['completedTime'] - process['arrivalTime']
        process['waitingTime'] = process['turnAroundTime'] - process['durationTime']
        completed_list.append(process)

    display_results(completed_list)
    render_cycle_table()

# Algoritmo Shortest Remaining Time First (SRTF)
def shortest_remaining_time_first():
    time = 0
    queue = []
    completed_list = []

    def add_to_queue():
        nonlocal queue
        for process in process_list[:]:
            if time >= process['arrivalTime']:
                if 'remainingTime' not in process:
                    process['remainingTime'] = process['durationTime']
                queue.append(process)
                process_list.remove(process)
        queue.sort(key=lambda x: x['remainingTime'])

    init_timeline_from_process_table()
    add_to_queue()
    while not queue and process_list:
        time += 1
        add_to_queue()
        log_cycle(time, None, [p['processID'] for p in queue])

    while process_list or queue:
        if not queue:
            time += 1
            add_to_queue()
            log_cycle(time, None, [p['processID'] for p in queue])
            continue

        # Elegimos el de menor restante y ejecutamos 1 ciclo
        add_to_queue()
        process = queue.pop(0)
        time += 1
        process['remainingTime'] -= 1
        log_cycle(time, process['processID'], [p['processID'] for p in queue])

        if process['remainingTime'] == 0:
            process['completedTime'] = time
            process['turnAroundTime'] = process['completedTime'] - process['arrivalTime']
            process['waitingTime'] = process['turnAroundTime'] - process['durationTime']
            completed_list.append(process)
        else:
            queue.append(process)
            queue.sort(key=lambda x: x['remainingTime'])

    display_results(completed_list)
    render_cycle_table()

# Algoritmo Round Robin
def round_robin():
    time = 0
    queue = []
    completed_list = []

    tq_text = time_quantum_entry.get()
    if not tq_text.strip():
        messagebox.showerror("Error", "Por favor, ingrese un valor para el Time Quantum")
        return
    time_quantum = int(tq_text)

    def add_to_queue():
        nonlocal queue
        for process in process_list[:]:
            if time >= process['arrivalTime']:
                if 'remainingTime' not in process:
                    process['remainingTime'] = process['durationTime']
                process['lastTimeQueued'] = time
                queue.append(process)
                process_list.remove(process)
        queue.sort(key=lambda x: [x['lastTimeQueued'], x['remainingTime'], x['arrivalTime']])

    init_timeline_from_process_table()
    add_to_queue()
    while not queue and process_list:
        time += 1
        add_to_queue()
        log_cycle(time, None, [p['processID'] for p in queue])

    while process_list or queue:
        if not queue:
            time += 1
            add_to_queue()
            log_cycle(time, None, [p['processID'] for p in queue])
            continue

        process = queue.pop(0)
        for _ in range(min(time_quantum, process['remainingTime'])):
            time += 1
            add_to_queue()
            process['remainingTime'] -= 1
            # === Ciclos ===
            log_cycle(time, process['processID'], [p['processID'] for p in queue])
            if process['remainingTime'] == 0:
                process['completedTime'] = time
                process['turnAroundTime'] = process['completedTime'] - process['arrivalTime']
                process['waitingTime'] = process['turnAroundTime'] - process['durationTime']
                completed_list.append(process)
                break
        if process.get('remainingTime', 0) > 0:
            process['lastTimeQueued'] = time
            queue.append(process)

    display_results(completed_list)
    render_cycle_table()

#########################################################################################

# Ocultar/Mostrar campo Time Quantum para el algoritmo Round Robin
def on_algorithm_change(event):
    if algorithm_selector.get() == 'Round Robin':
        time_quantum_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=5)
    else:
        time_quantum_entry.delete(0, 'end')
        time_quantum_frame.grid_forget()

# Añadir proceso a la tabla
def add_process():
    try:
        process_id = str(process_id_entry.get())
        arrival_time = int(arrival_time_entry.get())
        duration_time = int(duration_time_entry.get())

        if (process_id != '') and (arrival_time>=0) and (duration_time>0):
            process_table.insert("", "end", values=(process_id, arrival_time, duration_time))
            process_id_entry.delete(0, 'end')
            arrival_time_entry.delete(0, 'end')
            duration_time_entry.delete(0, 'end')
        else:
            raise ValueError("Faltan valores")
    except ValueError:
        messagebox.showerror("Error", "Por favor, ingrese valores válidos")

# Calcular resultados según algoritmo seleccionado
def calculate():
    # Limpiar resultados
    result_table.delete(*result_table.get_children())
    for w in cycle_container.winfo_children():
        w.destroy()

    global process_list
    process_list = []
    for child in process_table.get_children():
        process_list.append({
            'processID': process_table.item(child)['values'][0],
            'arrivalTime': process_table.item(child)['values'][1],
            'durationTime': process_table.item(child)['values'][2]
        })
    
    selected_algo = algorithm_selector.get()

    if selected_algo == 'FCFS':
        first_come_first_served()
    elif selected_algo == 'SJF':
        shortest_job_first()
    elif selected_algo == 'SRTF':
        shortest_remaining_time_first()
    elif selected_algo == 'Round Robin':
        round_robin()
    else:
        messagebox.showerror("Error", "Por favor, seleccione un algoritmo")

# Mostrar resultados en la tabla de resultados
def display_results(completed_list):
    for child in process_table.get_children():
        processID=process_table.item(child)['values'][0]
        for process in completed_list:
            if processID == process['processID']:
                result_table.insert("", "end", values=(
                    process['processID'],
                    process['arrivalTime'],
                    process['durationTime'],
                    process['completedTime'],
                    process['waitingTime'],
                    process['turnAroundTime']
                ))

    if not completed_list:
        avg_turnaround = 0.0
        avg_waiting = 0.0
    else:
        avg_turnaround = sum(p['turnAroundTime'] for p in completed_list) / len(completed_list)
        avg_waiting = sum(p['waitingTime'] for p in completed_list) / len(completed_list)

    avg_turnaround_entry.config(state='normal')
    avg_turnaround_entry.delete(0, 'end')
    avg_turnaround_entry.insert(0, f"{avg_turnaround:.2f}")
    avg_turnaround_entry.config(state='readonly')

    avg_waiting_entry.config(state='normal')
    avg_waiting_entry.delete(0, 'end')
    avg_waiting_entry.insert(0, f"{avg_waiting:.2f}")
    avg_waiting_entry.config(state='readonly')

if __name__ == "__main__":

    # Crear la ventana principal
    root = tk.Tk()
    root.title("Simulador de Algoritmos de Planificación")

    # Configuración de la ventana
    frame = tk.Frame(root)
    frame.pack(padx=10, pady=10)

    # Selección del algoritmo
    algorithm_selector_label = tk.Label(frame, text="Seleccionar Algoritmo:")
    algorithm_selector_label.grid(row=0, column=0, padx=5, pady=5)
    algorithm_selector = ttk.Combobox(frame, values=["FCFS", "SJF", "SRTF", "Round Robin"], state="readonly")
    algorithm_selector.grid(row=0, column=1, padx=5, pady=5)
    algorithm_selector.bind("<<ComboboxSelected>>", on_algorithm_change)

    # Campo Time Quantum (oculto inicialmente)
    time_quantum_frame = tk.Frame(frame)
    time_quantum_label = tk.Label(time_quantum_frame, text="Time Quantum:")
    time_quantum_label.grid(row=0, column=0, padx=10, pady=5)
    time_quantum_entry = tk.Entry(time_quantum_frame)
    time_quantum_entry.grid(row=0, column=1, padx=10, pady=5)
    time_quantum_frame.grid_forget()

    # Campos para añadir proceso
    process_id_label = tk.Label(frame, text="ID del Proceso:")
    process_id_label.grid(row=1, column=0, padx=5, pady=5)
    process_id_entry = tk.Entry(frame)
    process_id_entry.grid(row=1, column=1, padx=5, pady=5)

    arrival_time_label = tk.Label(frame, text="Tiempo de Llegada:")
    arrival_time_label.grid(row=2, column=0, padx=5, pady=5)
    arrival_time_entry = tk.Entry(frame)
    arrival_time_entry.grid(row=2, column=1, padx=5, pady=5)

    duration_time_label = tk.Label(frame, text="Tiempo de Duración:")
    duration_time_label.grid(row=3, column=0, padx=5, pady=5)
    duration_time_entry = tk.Entry(frame)
    duration_time_entry.grid(row=3, column=1, padx=5, pady=5)

    # Botón para añadir proceso
    add_process_button = tk.Button(frame, text="Añadir Proceso", command=add_process)
    add_process_button.grid(row=4, columnspan=2, pady=10)

    # Tabla de procesos añadidos
    process_table = ttk.Treeview(frame, columns=("ID", "Llegada", "Duración"), show="headings")
    process_table.heading("ID", text="ID")
    process_table.heading("Llegada", text="Llegada")
    process_table.heading("Duración", text="Duración")
    process_table.grid(row=5, columnspan=2, pady=10)

    # Botón para calcular
    calculate_button = tk.Button(frame, text="Calcular", command=calculate)
    calculate_button.grid(row=6, columnspan=2, pady=10)

    # Tabla de resultados
    result_table = ttk.Treeview(frame, columns=("ID", "Llegada", "Duración", "Completado", "Espera", "Retorno"), show="headings")
    result_table.heading("ID", text="ID")
    result_table.heading("Llegada", text="Llegada")
    result_table.heading("Duración", text="Duración")
    result_table.heading("Completado", text="Completado")
    result_table.heading("Espera", text="Espera")
    result_table.heading("Retorno", text="Retorno")
    result_table.grid(row=7, columnspan=2, pady=10)

    # Promedios
    avg_waiting_label = tk.Label(frame, text="Promedio Espera:")
    avg_waiting_label.grid(row=8, column=0, padx=5, pady=5)
    avg_waiting_entry = tk.Entry(frame, state='readonly')
    avg_waiting_entry.grid(row=8, column=1, padx=5, pady=5)

    avg_turnaround_label = tk.Label(frame, text="Promedio Retorno:")
    avg_turnaround_label.grid(row=9, column=0, padx=5, pady=5)
    avg_turnaround_entry = tk.Entry(frame, state='readonly')
    avg_turnaround_entry.grid(row=9, column=1, padx=5, pady=5)

    # ======== Contenedor de la tabla de ciclos ========
    cycle_title = tk.Label(frame, text="Tabla de ciclos (X: ejecuta, O: espera)")
    cycle_title.grid(row=10, column=0, columnspan=2, pady=(10,2))
    cycle_container = tk.Frame(frame, width=800, height=260, relief="groove", bd=2)
    cycle_container.grid(row=11, column=0, columnspan=2, sticky="nsew", pady=(0,10))

    process_list = []

    # Botones limpiar/reset
    def clear_results_only():
        result_table.delete(*result_table.get_children())
        for w in cycle_container.winfo_children():
            w.destroy()
        process_list.clear()
        avg_turnaround_entry.config(state='normal')
        avg_turnaround_entry.delete(0, 'end')
        avg_turnaround_entry.config(state='readonly')
        avg_waiting_entry.config(state='normal')
        avg_waiting_entry.delete(0, 'end')
        avg_waiting_entry.config(state='readonly')

    clear_button = tk.Button(frame, text="Limpiar resultados", command=clear_results_only)

    def reset_all():
        process_table.delete(*process_table.get_children())
        clear_results_only()
        process_id_entry.delete(0, 'end')
        arrival_time_entry.delete(0, 'end')
        duration_time_entry.delete(0, 'end')
        time_quantum_entry.delete(0, 'end')

    reset_button = tk.Button(frame, text="Resetear todo", command=reset_all)
    
    clear_button.grid(row=12, column=0, pady=10)
    reset_button.grid(row=12, column=1, pady=10)

    root.mainloop()
