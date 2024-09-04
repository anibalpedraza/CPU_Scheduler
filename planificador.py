import tkinter as tk
from tkinter import messagebox, ttk

# =======================================
#   Estructuras para la TABLA DE CICLOS
# =======================================
timeline_data = {}        # {pid: ['','X','O', ...]}
arrival_marks = {}        # {pid: int_col | 0 si llegada en 0 (sombrear celda del nombre)}
proc_info = {}            # {pid: {'arrivalTime': int, 'durationTime': int}}
total_time = 0
all_pids = []
current_algo = "Planificador"

def init_timeline_from_process_table(algo_name: str):
    """Inicializa las estructuras de la 'tabla de ciclos' a partir de la tabla de procesos."""
    global timeline_data, arrival_marks, total_time, all_pids, proc_info, current_algo
    current_algo = algo_name
    timeline_data, arrival_marks, proc_info = {}, {}, {}
    total_time = 0
    all_pids = []
    for child in process_table.get_children():
        pid = str(process_table.item(child)['values'][0])
        arr = int(process_table.item(child)['values'][1])
        dur = int(process_table.item(child)['values'][2])
        all_pids.append(pid)
        timeline_data[pid] = []
        arrival_marks[pid] = int(arr)  # sombreado exactamente en el ciclo de llegada (si es 0 => se sombreará la celda del nombre)
        proc_info[pid] = {'arrivalTime': arr, 'durationTime': dur}

def _ensure_len(pid, t):
    while len(timeline_data[pid]) < t:
        timeline_data[pid].append('')

def log_cycle(t, running_pid, queue_pids):
    """Registra el estado del ciclo t.
    - Se marca 'X' para el proceso en ejecución.
    - Se marca 'O' para procesos en la cola cuyo arrivalTime < t (no se marca espera en el ciclo de llegada).
    """
    global total_time
    for pid in all_pids:
        _ensure_len(pid, t)
        if pid == running_pid:
            timeline_data[pid][t-1] = 'X'
        elif pid in queue_pids and proc_info.get(pid, {}).get('arrivalTime', 1e9) < t:
            # Solo marcar espera a partir del ciclo siguiente al de llegada
            if timeline_data[pid][t-1] == '':
                timeline_data[pid][t-1] = 'O'
    total_time = max(total_time, t)

def render_cycle_table():
    """Dibuja la rejilla con scroll horizontal y sombreado de llegadas."""
    # limpiar
    for w in cycle_container.winfo_children():
        w.destroy()

    if total_time == 0 or not all_pids:
        return

    canvas = tk.Canvas(cycle_container, height=260)
    hscroll = tk.Scrollbar(cycle_container, orient='horizontal', command=canvas.xview)
    canvas.configure(xscrollcommand=hscroll.set)
    canvas.grid(row=0, column=0, sticky="nsew")
    hscroll.grid(row=1, column=0, sticky="ew")
    cycle_container.grid_rowconfigure(0, weight=1)
    cycle_container.grid_columnconfigure(0, weight=1)

    grid = tk.Frame(canvas)
    canvas.create_window((0, 0), window=grid, anchor="nw")

    # Cabecera
    tk.Label(grid, text=current_algo, width=14, anchor="w").grid(row=0, column=0, sticky="nsew")
    for c in range(1, total_time+1):
        tk.Label(grid, text=str(c), relief="raised").grid(row=0, column=c, sticky="nsew")

    # Filas
    for r, pid in enumerate(all_pids, start=1):
        # Nombre del proceso (con sombreado si llegada=0)
        name_bg = "#d9d9d9" if arrival_marks.get(pid, 1) == 0 else "SystemButtonFace"
        tk.Label(grid, text=pid, anchor="w", relief="groove", bg=name_bg).grid(row=r, column=0, sticky="nsew")
        row_vals = timeline_data.get(pid, [])
        for c in range(1, total_time+1):
            txt = row_vals[c-1] if c-1 < len(row_vals) else ''
            bg = "SystemButtonFace"
            # sombreado del ciclo de llegada (si llegada>0)
            if arrival_marks.get(pid, -1) == c:
                bg = "#d9d9d9"
            tk.Label(grid, text=txt, width=2, relief="groove", bg=bg).grid(row=r, column=c, sticky="nsew")

    grid.update_idletasks()
    canvas.configure(scrollregion=canvas.bbox("all"))

# =====================
#   Algoritmos
# =====================

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

    init_timeline_from_process_table('FCFS')
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
        process['turnAroundTime'] = time - process['arrivalTime']
        process['waitingTime'] = process['turnAroundTime'] - process['durationTime']
        completed_list.append(process)

    display_results(completed_list)
    render_cycle_table()

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

    init_timeline_from_process_table('SJF')
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
        process['turnAroundTime'] = time - process['arrivalTime']
        process['waitingTime'] = process['turnAroundTime'] - process['durationTime']
        completed_list.append(process)

    display_results(completed_list)
    render_cycle_table()

def shortest_remaining_time_first():
    """Preemptivo, ejecuta de a 1 ciclo y reordena por restante. 
    La espera se marca solo para procesos con arrivalTime < t (no en el ciclo de llegada)."""
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

    init_timeline_from_process_table('SRTF')
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

        add_to_queue()
        process = queue.pop(0)
        # Ejecuta 1 ciclo
        time += 1
        process['remainingTime'] -= 1
        log_cycle(time, process['processID'], [p['processID'] for p in queue])

        if process['remainingTime'] == 0:
            process['completedTime'] = time
            process['turnAroundTime'] = time - process['arrivalTime']
            process['waitingTime'] = process['turnAroundTime'] - process['durationTime']
            completed_list.append(process)
        else:
            queue.append(process)
            queue.sort(key=lambda x: x['remainingTime'])

    display_results(completed_list)
    render_cycle_table()

def round_robin():
    """Round Robin con quantum fijo. 
    La espera se marca solo si arrivalTime < t (no en el ciclo de llegada)."""
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
                queue.append(process)
                process_list.remove(process)

    init_timeline_from_process_table('Round Robin')
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
        ran = 0
        while ran < time_quantum and process['remainingTime'] > 0:
            time += 1
            add_to_queue()  # llegan nuevos al inicio de cada ciclo
            process['remainingTime'] -= 1
            ran += 1
            log_cycle(time, process['processID'], [p['processID'] for p in queue])

        if process['remainingTime'] == 0:
            process['completedTime'] = time
            process['turnAroundTime'] = time - process['arrivalTime']
            process['waitingTime'] = process['turnAroundTime'] - process['durationTime']
            completed_list.append(process)
        else:
            # vuelve al final de la cola
            queue.append(process)

    display_results(completed_list)
    render_cycle_table()

# =======================================
#     Lógica de interfaz / común
# =======================================

def on_algorithm_change(event):
    if algorithm_selector.get() == 'Round Robin':
        time_quantum_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=5)
    else:
        time_quantum_entry.delete(0, 'end')
        time_quantum_frame.grid_forget()

def add_process():
    try:
        process_id = str(process_id_entry.get())
        arrival_time = int(arrival_time_entry.get())
        duration_time = int(duration_time_entry.get())

        if (process_id != '') and (arrival_time >= 0) and (duration_time > 0):
            process_table.insert("", "end", values=(process_id, arrival_time, duration_time))
            process_id_entry.delete(0, 'end')
            arrival_time_entry.delete(0, 'end')
            duration_time_entry.delete(0, 'end')
        else:
            raise ValueError("Faltan valores")
    except ValueError:
        messagebox.showerror("Error", "Por favor, ingrese valores válidos")

def calculate():
    # Limpiar resultados previos
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

def display_results(completed_list):
    for child in process_table.get_children():
        processID = process_table.item(child)['values'][0]
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
    root = tk.Tk()
    root.title("Simulador de Algoritmos de Planificación")

    frame = tk.Frame(root)
    frame.pack(padx=10, pady=10)

    algorithm_selector_label = tk.Label(frame, text="Seleccionar Algoritmo:")
    algorithm_selector_label.grid(row=0, column=0, padx=5, pady=5)
    algorithm_selector = ttk.Combobox(frame, values=["FCFS", "SJF", "SRTF", "Round Robin"], state="readonly")
    algorithm_selector.grid(row=0, column=1, padx=5, pady=5)
    algorithm_selector.bind("<<ComboboxSelected>>", on_algorithm_change)

    time_quantum_frame = tk.Frame(frame)
    time_quantum_label = tk.Label(time_quantum_frame, text="Time Quantum:")
    time_quantum_label.grid(row=0, column=0, padx=10, pady=5)
    time_quantum_entry = tk.Entry(time_quantum_frame)
    time_quantum_entry.grid(row=0, column=1, padx=10, pady=5)
    time_quantum_frame.grid_forget()

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

    add_process_button = tk.Button(frame, text="Añadir Proceso", command=add_process)
    add_process_button.grid(row=4, columnspan=2, pady=10)

    process_table = ttk.Treeview(frame, columns=("ID", "Llegada", "Duración"), show="headings")
    process_table.heading("ID", text="ID")
    process_table.heading("Llegada", text="Llegada")
    process_table.heading("Duración", text="Duración")
    process_table.grid(row=5, columnspan=2, pady=10)

    calculate_button = tk.Button(frame, text="Calcular", command=calculate)
    calculate_button.grid(row=6, columnspan=2, pady=10)

    result_table = ttk.Treeview(frame, columns=("ID", "Llegada", "Duración", "Completado", "Espera", "Retorno"), show="headings")
    result_table.heading("ID", text="ID")
    result_table.heading("Llegada", text="Llegada")
    result_table.heading("Duración", text="Duración")
    result_table.heading("Completado", text="Completado")
    result_table.heading("Espera", text="Espera")
    result_table.heading("Retorno", text="Retorno")
    result_table.grid(row=7, columnspan=2, pady=10)

    avg_waiting_label = tk.Label(frame, text="Promedio Espera:")
    avg_waiting_label.grid(row=8, column=0, padx=5, pady=5)
    avg_waiting_entry = tk.Entry(frame, state='readonly')
    avg_waiting_entry.grid(row=8, column=1, padx=5, pady=5)

    avg_turnaround_label = tk.Label(frame, text="Promedio Retorno:")
    avg_turnaround_label.grid(row=9, column=0, padx=5, pady=5)
    avg_turnaround_entry = tk.Entry(frame, state='readonly')
    avg_turnaround_entry.grid(row=9, column=1, padx=5, pady=5)

    cycle_title = tk.Label(frame, text="Tabla de ciclos (X: ejecuta, O: espera)")
    cycle_title.grid(row=10, column=0, columnspan=2, pady=(10,2))
    cycle_container = tk.Frame(frame, width=800, height=260, relief="groove", bd=2)
    cycle_container.grid(row=11, column=0, columnspan=2, sticky="nsew", pady=(0,10))

    process_list = []

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

    def reset_all():
        process_table.delete(*process_table.get_children())
        clear_results_only()
        process_id_entry.delete(0, 'end')
        arrival_time_entry.delete(0, 'end')
        duration_time_entry.delete(0, 'end')
        time_quantum_entry.delete(0, 'end')

    clear_button = tk.Button(frame, text="Limpiar resultados", command=clear_results_only)
    reset_button = tk.Button(frame, text="Resetear todo", command=reset_all)

    clear_button.grid(row=12, column=0, pady=10)
    reset_button.grid(row=12, column=1, pady=10)

    root.mainloop()
