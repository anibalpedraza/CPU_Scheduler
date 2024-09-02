import tkinter as tk
from tkinter import messagebox, ttk

# Algoritmo First-Come, First-Served (FCFS)
def first_come_first_served():
    time = -1
    queue = []
    completed_list = []

    def add_to_queue():
        nonlocal queue
        for process in process_list[:]:
            if time >= process['arrivalTime']:
                queue.append(process)
                process_list.remove(process)

    while process_list or queue:
        while not queue:
            time += 1
            add_to_queue()

        process = queue.pop(0)
        for _ in range(process['durationTime']):
            time += 1
            add_to_queue()

        process['completedTime'] = time
        process['turnAroundTime'] = process['completedTime'] - process['arrivalTime']
        process['waitingTime'] = process['turnAroundTime'] - process['durationTime']
        completed_list.append(process)

    display_results(completed_list)

# Algoritmo Shortest Job First (SJF)
def shortest_job_first():
    time = -1
    queue = []
    completed_list = []

    def add_to_queue():
        nonlocal queue
        for process in process_list[:]:
            if time >= process['arrivalTime']:
                queue.append(process)
                process_list.remove(process)
        queue.sort(key=lambda x: x['durationTime'])

    while process_list or queue:
        while not queue:
            time += 1
            add_to_queue()

        process = queue.pop(0)
        for _ in range(process['durationTime']):
            time += 1
            add_to_queue()

        process['completedTime'] = time
        process['turnAroundTime'] = process['completedTime'] - process['arrivalTime']
        process['waitingTime'] = process['turnAroundTime'] - process['durationTime']
        completed_list.append(process)

    display_results(completed_list)

# Algoritmo Shortest Remaining Time First (SRTF)
def shortest_remaining_time_first():
    time = -1
    queue = []
    completed_list = []

    def add_to_queue():
        nonlocal queue
        for process in process_list[:]:
            if time >= process['arrivalTime']:
                process['remainingTime'] = process['durationTime']
                queue.append(process)
                process_list.remove(process)
        queue.sort(key=lambda x: x['remainingTime'])

    while process_list or queue:
        while not queue:
            time += 1
            add_to_queue()

        #queue.sort(key=lambda x: x['remainingTime'])
        time += 1

        process = queue.pop(0)
        process['remainingTime'] -= 1

        if process['remainingTime'] == 0:
            process['completedTime'] = time
            process['turnAroundTime'] = process['completedTime'] - process['arrivalTime']
            process['waitingTime'] = process['turnAroundTime'] - process['durationTime']
            completed_list.append(process)
        else:
            queue.append(process)
        
        add_to_queue()

    display_results(completed_list)

# Algoritmo Round Robin
def round_robin():
    time = -1
    queue = []
    completed_list = []

    time_quantum = int(time_quantum_entry.get())
    if not time_quantum:
        messagebox.showerror("Error", "Por favor, ingrese un valor para el Time Quantum")
        return

    def add_to_queue():
        nonlocal queue
        for process in process_list[:]:
            if time >= process['arrivalTime']:
                process['remainingTime'] = process['durationTime']
                process['lastTimeQueued'] = time
                queue.append(process)
                process_list.remove(process)
        queue.sort(key=lambda x: [x['lastTimeQueued'],x['remainingTime'],x['arrivalTime']])

    while process_list or queue:
        while not queue:
            time += 1
            add_to_queue()

        process = queue.pop(0)
        for _ in range(min(time_quantum, process['remainingTime'])):
            time += 1
            add_to_queue()
            process['remainingTime'] -= 1
            if process['remainingTime'] == 0:
                process['completedTime'] = time
                process['turnAroundTime'] = process['completedTime'] - process['arrivalTime']
                process['waitingTime'] = process['turnAroundTime'] - process['durationTime']
                completed_list.append(process)
                #break
        if process['remainingTime'] > 0:
            process['lastTimeQueued'] = time
            queue.append(process)

    display_results(completed_list)

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
            #process_list.append({'processID': process_id, 'arrivalTime': arrival_time, 'durationTime': duration_time})
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
    '''
    if not process_list:
        messagebox.showwarning("Advertencia", "Por favor, inserte algunos procesos")
        return
    '''

    # Limpieza de la tabla de resultados
    result_table.delete(*result_table.get_children())

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

    avg_turnaround = sum(p['turnAroundTime'] for p in completed_list) / len(completed_list)
    avg_waiting = sum(p['waitingTime'] for p in completed_list) / len(completed_list)
    max_completed_time = max(p['completedTime'] for p in completed_list)
    #throughput = len(completed_list) / max_completed_time

    avg_turnaround_entry.config(state='normal')
    avg_turnaround_entry.delete(0, 'end')
    avg_turnaround_entry.insert(0, f"{avg_turnaround:.2f}")
    avg_turnaround_entry.config(state='readonly')

    avg_waiting_entry.config(state='normal')
    avg_waiting_entry.delete(0, 'end')
    avg_waiting_entry.insert(0, f"{avg_waiting:.2f}")
    avg_waiting_entry.config(state='readonly')
    '''
    throughput_entry.config(state='normal')
    throughput_entry.delete(0, 'end')
    throughput_entry.insert(0, f"{throughput:.2f}")
    throughput_entry.config(state='readonly')
    '''

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

    '''
    throughput_label = tk.Label(frame, text="Throughput:")
    throughput_label.grid(row=10, column=0, padx=5, pady=5)
    throughput_entry = tk.Entry(frame, state='readonly')
    throughput_entry.grid(row=10, column=1, padx=5, pady=5)
    '''

    process_list = []

    # Boton para limpiar los resultados, manteniendo los procesos añadidos
    clear_button = tk.Button(frame, text="Limpiar resultados", command=lambda:
                                [result_table.delete(*result_table.get_children()),
                                process_list.clear(),
                                avg_turnaround_entry.config(state='normal'),
                                avg_turnaround_entry.delete(0, 'end'),
                                avg_turnaround_entry.config(state='readonly'),
                                avg_waiting_entry.config(state='normal'),
                                avg_waiting_entry.delete(0, 'end'),
                                avg_waiting_entry.config(state='readonly')])

    # Botón para resetear todo
    reset_button = tk.Button(frame, text="Resetear todo", command=lambda:
                             [process_table.delete(*process_table.get_children()),
                              result_table.delete(*result_table.get_children()),
                              process_list.clear(),
                              avg_turnaround_entry.config(state='normal'),
                              avg_turnaround_entry.delete(0, 'end'),
                              avg_turnaround_entry.config(state='readonly'),
                              avg_waiting_entry.config(state='normal'),
                              avg_waiting_entry.delete(0, 'end'),
                              avg_waiting_entry.config(state='readonly'),
                              #throughput_entry.delete(0, 'end'),
                              process_id_entry.delete(0, 'end'),
                              arrival_time_entry.delete(0, 'end'),
                              duration_time_entry.delete(0, 'end'),
                              time_quantum_entry.delete(0, 'end')])
    
    clear_button.grid(row=11, column=0, pady=10)
    reset_button.grid(row=11, column=1, pady=10)

    root.mainloop()
