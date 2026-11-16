import sqlite3
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk


# 1. Configurarea bazei de date și a tabelelor pentru echipamente, programări și finanțe
class CMMSDatabase:

  def __init__(self, db_name="cmms_plant.db"):
    self.conn = sqlite3.connect(db_name)
    self.cursor = self.conn.cursor()
    self.create_tables()

  def create_tables(self):
    self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS echipamente (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nume TEXT NOT NULL,
                serie TEXT UNIQUE NOT NULL,
                locatie TEXT NOT NULL
            )
        """)
    self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS mentenanta (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                echipament_id INTEGER,
                tip_revizie TEXT NOT NULL,
                data_inceput TEXT NOT NULL,
                data_sfarsit TEXT NOT NULL,
                status TEXT DEFAULT 'Programata',
                FOREIGN KEY (echipament_id) REFERENCES echipamente (id)
            )
        """)
    self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS devize (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mentenanta_id INTEGER,
                piese_cost REAL DEFAULT 0.0,
                manopera_cost REAL DEFAULT 0.0,
                suma_achitata REAL DEFAULT 0.0,
                FOREIGN KEY (mentenanta_id) REFERENCES mentenanta (id)
            )
        """)
    self.conn.commit()


class CMMSApp:

  def __init__(self, root):
    self.db = CMMSDatabase()
    self.root = root
    self.root.title(
        "Sistem de Gestiune și Planificare Mentenanță Echipamente (CMMS)"
    )
    self.root.geometry("1100x700")
    self.root.minsize(950, 600)

    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        "TNotebook.Tab", font=("Arial", 11, "bold"), padding=[12, 8]
    )
    style.configure("Treeview.Heading", font=("Arial", 10, "bold"))

    self.notebook = ttk.Notebook(root)
    self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    self.tab_echipamente = ttk.Frame(self.notebook)
    self.tab_calendar = ttk.Frame(self.notebook)
    self.tab_financiar = ttk.Frame(self.notebook)

    self.notebook.add(self.tab_echipamente, text="⚙️ Echipamente")
    self.notebook.add(self.tab_calendar, text="📅 Programări & Calendar")
    self.notebook.add(self.tab_financiar, text="💰 Financiar & Devize")

    self.init_echipamente_tab()
    self.init_calendar_tab()
    self.init_financiar_tab()

    self.refresh_all_data()

  # 2. Prima etapă: Gestiunea echipamentelor (adăugare, vizualizare, ștergere)
  def init_echipamente_tab(self):
    frame_form = ttk.LabelFrame(
        self.tab_echipamente, text=" Adăugare Echipament Nou ", padding=15
    )
    frame_form.pack(fill=tk.X, padx=15, pady=15)

    ttk.Label(frame_form, text="Nume Echipament:", font=("Arial", 10)).grid(
        row=0, column=0, sticky=tk.W, padx=5, pady=5
    )
    self.entry_eq_nume = ttk.Entry(frame_form, width=25)
    self.entry_eq_nume.grid(row=0, column=1, padx=5, pady=5)

    ttk.Label(frame_form, text="Număr Serie:", font=("Arial", 10)).grid(
        row=0, column=2, sticky=tk.W, padx=5, pady=5
    )
    self.entry_eq_serie = ttk.Entry(frame_form, width=25)
    self.entry_eq_serie.grid(row=0, column=3, padx=5, pady=5)

    ttk.Label(frame_form, text="Locație / Linie:", font=("Arial", 10)).grid(
        row=0, column=4, sticky=tk.W, padx=5, pady=5
    )
    self.entry_eq_locatie = ttk.Entry(frame_form, width=25)
    self.entry_eq_locatie.grid(row=0, column=5, padx=5, pady=5)

    btn_adauga_eq = ttk.Button(
        frame_form, text="Salvează Echipament", command=self.adauga_echipament
    )
    btn_adauga_eq.grid(row=0, column=6, padx=15, pady=5)

    frame_table = ttk.LabelFrame(
        self.tab_echipamente, text=" Lista Echipamente Înregistrate ", padding=15
    )
    frame_table.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

    columns = ("ID", "Nume", "Serie", "Locație")
    self.tree_echipamente = ttk.Treeview(
        frame_table, columns=columns, show="headings", height=15
    )
    for col in columns:
      self.tree_echipamente.heading(col, text=col)
      self.tree_echipamente.column(col, width=150, anchor=tk.CENTER)
    self.tree_echipamente.column("ID", width=60)

    scrollbar = ttk.Scrollbar(
        frame_table,
        orient=tk.VERTICAL,
        command=self.tree_echipamente.yview,
    )
    self.tree_echipamente.configure(yscrollcommand=scrollbar.set)
    self.tree_echipamente.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    btn_sterge_eq = ttk.Button(
        frame_table,
        text="Șterge Echipamentul Selectat",
        command=self.sterge_echipament,
    )
    btn_sterge_eq.pack(side=tk.BOTTOM, anchor=tk.E, pady=10)

  def adauga_echipament(self):
    nume = self.entry_eq_nume.get().strip()
    serie = self.entry_eq_serie.get().strip()
    locatie = self.entry_eq_locatie.get().strip()

    if not nume or not serie or not locatie:
      messagebox.showerror(
          "Eroare Validare", "Toate câmpurile sunt obligatorii!"
      )
      return

    try:
      self.db.cursor.execute(
          "INSERT INTO echipamente (nume, serie, locatie) VALUES (?, ?, ?)",
          (nume, serie, locatie),
      )
      self.db.conn.commit()
      messagebox.showinfo(
          "Succes", "Echipamentul a fost înregistrat cu succes!"
      )
      self.entry_eq_nume.delete(0, tk.END)
      self.entry_eq_serie.delete(0, tk.END)
      self.entry_eq_locatie.delete(0, tk.END)
      self.refresh_all_data()
    except sqlite3.IntegrityError:
      messagebox.showerror(
          "Eroare", f"Echipamentul cu seria '{serie}' există deja în baza de date!"
      )

  def sterge_echipament(self):
    selected = self.tree_echipamente.selection()
    if not selected:
      messagebox.showwarning(
          "Atenție", "Selectați un echipament din listă pentru ștergere!"
      )
      return

    eq_id = self.tree_echipamente.item(selected[0])["values"][0]
    if messagebox.askyesno(
        "Confirmare",
        "Ștergerea echipamentului va elimina și istoricul de mentenanță și"
        " devizele asociate. Continuați?",
    ):
      self.db.cursor.execute(
          "DELETE FROM devize WHERE mentenanta_id IN (SELECT id FROM mentenanta"
          " WHERE echipament_id = ?)",
          (eq_id,),
      )
      self.db.cursor.execute(
          "DELETE FROM mentenanta WHERE echipament_id = ?", (eq_id,)
      )
      self.db.cursor.execute("DELETE FROM echipamente WHERE id = ?", (eq_id,))
      self.db.conn.commit()
      messagebox.showinfo("Succes", "Echipamentul a fost șters.")
      self.refresh_all_data()

  # 3. A doua etapă: Calendarul inteligent și prevenirea suprapunerilor orare
  def init_calendar_tab(self):
    frame_form = ttk.LabelFrame(
        self.tab_calendar,
        text=" Programare Fereastră Mentenanță (Anti-Suprapunere) ",
        padding=15,
    )
    frame_form.pack(fill=tk.X, padx=15, pady=15)

    ttk.Label(frame_form, text="Echipament:", font=("Arial", 10)).grid(
        row=0, column=0, sticky=tk.W, padx=5, pady=5
    )
    self.combo_eq = ttk.Combobox(frame_form, state="readonly", width=25)
    self.combo_eq.grid(row=0, column=1, padx=5, pady=5)

    ttk.Label(frame_form, text="Tip Revizie/Intervenție:", font=("Arial", 10)).grid(
        row=0, column=2, sticky=tk.W, padx=5, pady=5
    )
    self.entry_tip_revizie = ttk.Entry(frame_form, width=22)
    self.entry_tip_revizie.grid(row=0, column=3, padx=5, pady=5)

    ttk.Label(
        frame_form, text="Start (YYYY-MM-DD HH:MM):", font=("Arial", 10)
    ).grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
    self.entry_start = ttk.Entry(frame_form, width=25)
    self.entry_start.insert(0, datetime.now().strftime("%Y-%m-%d 08:00"))
    self.entry_start.grid(row=1, column=1, padx=5, pady=5)

    ttk.Label(
        frame_form, text="Sfârșit (YYYY-MM-DD HH:MM):", font=("Arial", 10)
    ).grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
    self.entry_end = ttk.Entry(frame_form, width=22)
    self.entry_end.insert(0, datetime.now().strftime("%Y-%m-%d 16:00"))
    self.entry_end.grid(row=1, column=3, padx=5, pady=5)

    btn_programeaza = ttk.Button(
        frame_form,
        text="Programează Fereastra",
        command=self.programeaza_mentenanta,
    )
    btn_programeaza.grid(row=1, column=4, padx=15, pady=5)

    frame_table = ttk.LabelFrame(
        self.tab_calendar,
        text=" Calendar Intervenții Programate ",
        padding=15,
    )
    frame_table.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

    columns = (
        "ID",
        "Echipament",
        "Tip Revizie",
        "Data Început",
        "Data Sfârșit",
        "Status",
    )
    self.tree_mentenanta = ttk.Treeview(
        frame_table, columns=columns, show="headings", height=13
    )
    for col in columns:
      self.tree_mentenanta.heading(col, text=col)
      self.tree_mentenanta.column(col, width=150, anchor=tk.CENTER)
    self.tree_mentenanta.column("ID", width=50)

    scrollbar = ttk.Scrollbar(
        frame_table,
        orient=tk.VERTICAL,
        command=self.tree_mentenanta.yview,
    )
    self.tree_mentenanta.configure(yscrollcommand=scrollbar.set)
    self.tree_mentenanta.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    btn_anuleaza = ttk.Button(
        frame_table,
        text="Anulează / Șterge Programarea",
        command=self.anuleaza_mentenanta,
    )
    btn_anuleaza.pack(side=tk.BOTTOM, anchor=tk.E, pady=10)

  def verifica_suprapunere(self, eq_id, start_str, end_str):
    query = """
            SELECT id FROM mentenanta 
            WHERE echipament_id = ? AND status != 'Anulata'
            AND NOT (data_sfarsit <= ? OR data_inceput >= ?)
        """
    self.db.cursor.execute(query, (eq_id, start_str, end_str))
    return self.db.cursor.fetchone() is not None

  def programeaza_mentenanta(self):
    eq_selection = self.combo_eq.get()
    tip_revizie = self.entry_tip_revizie.get().strip()
    start_str = self.entry_start.get().strip()
    end_str = self.entry_end.get().strip()

    if not eq_selection or not tip_revizie or not start_str or not end_str:
      messagebox.showerror(
          "Eroare Validare", "Completați toate câmpurile pentru programare!"
      )
      return

    try:
      datetime.strptime(start_str, "%Y-%m-%d %H:%M")
      datetime.strptime(end_str, "%Y-%m-%d %H:%M")
    except ValueError:
      messagebox.showerror(
          "Format Gresit",
          "Formatul datelor trebuie să fie obligatoriu: YYYY-MM-DD HH:MM",
      )
      return

    if start_str >= end_str:
      messagebox.showerror(
          "Eroare", "Data de început trebuie să fie anterioară datei de sfârșit!"
      )
      return

    eq_id = int(eq_selection.split(" - ")[0])

    if self.verifica_suprapunere(eq_id, start_str, end_str):
      messagebox.showerror(
          "Conflict de Programare",
          "Echipamentul are deja o fereastră de mentenanță programată în"
          " acest interval! Evitați suprapunerile.",
      )
      return

    self.db.cursor.execute(
        """
            INSERT INTO mentenanta (echipament_id, tip_revizie, data_inceput, data_sfarsit, status)
            VALUES (?, ?, ?, ?, 'Programata')
        """,
        (eq_id, tip_revizie, start_str, end_str),
    )
    ment_id = self.db.cursor.lastrowid

    self.db.cursor.execute(
        """
            INSERT INTO devize (mentenanta_id, piese_cost, manopera_cost, suma_achitata)
            VALUES (?, 0.0, 0.0, 0.0)
        """,
        (ment_id,),
    )
    self.db.conn.commit()

    messagebox.showinfo(
        "Succes",
        "Fereastra de mentenanță a fost programată cu succes și s-a generat"
        " devizul aferent!",
    )
    self.entry_tip_revizie.delete(0, tk.END)
    self.refresh_all_data()

  def anuleaza_mentenanta(self):
    selected = self.tree_mentenanta.selection()
    if not selected:
      messagebox.showwarning(
          "Atenție", "Selectați o programare din calendar pentru anulare!"
      )
      return

    ment_id = self.tree_mentenanta.item(selected[0])["values"][0]
    if messagebox.askyesno(
        "Confirmare",
        "Sigur doriți să ștergeți această programare și devizul asociat?",
    ):
      self.db.cursor.execute("DELETE FROM devize WHERE mentenanta_id = ?", (ment_id,))
      self.db.cursor.execute("DELETE FROM mentenanta WHERE id = ?", (ment_id,))
      self.db.conn.commit()
      messagebox.showinfo("Succes", "Programarea a fost eliminată.")
      self.refresh_all_data()

  # 4. A treia etapă: Modulul financiar, devizele și calculul automat al restului de plată
  def init_financiar_tab(self):
    frame_table = ttk.LabelFrame(
        self.tab_financiar,
        text=" Evidență Financiară și Calcul Automat Rest de Plată ",
        padding=15,
    )
    frame_table.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

    columns = (
        "Deviz ID",
        "Echipament",
        "Intervenție",
        "Cost Piese (RON)",
        "Cost Manoperă (RON)",
        "Total Deviz (RON)",
        "Achitat (RON)",
        "Rest de Plată (RON)",
    )
    self.tree_devize = ttk.Treeview(
        frame_table, columns=columns, show="headings", height=12
    )
    for col in columns:
      self.tree_devize.heading(col, text=col)
      self.tree_devize.column(col, width=130, anchor=tk.CENTER)
    self.tree_devize.column("Deviz ID", width=70)

    scrollbar = ttk.Scrollbar(
        frame_table, orient=tk.VERTICAL, command=self.tree_devize.yview
    )
    self.tree_devize.configure(yscrollcommand=scrollbar.set)
    self.tree_devize.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    frame_edit = ttk.LabelFrame(
        self.tab_financiar, text=" Actualizare Suma Achitată și Costuri ", padding=15
    )
    frame_edit.pack(fill=tk.X, padx=15, pady=5)

    ttk.Label(frame_edit, text="Cost Piese (RON):").grid(
        row=0, column=0, sticky=tk.W, padx=5, pady=5
    )
    self.entry_piese = ttk.Entry(frame_edit, width=15)
    self.entry_piese.grid(row=0, column=1, padx=5, pady=5)

    ttk.Label(frame_edit, text="Cost Manoperă (RON):").grid(
        row=0, column=2, sticky=tk.W, padx=5, pady=5
    )
    self.entry_manopera = ttk.Entry(frame_edit, width=15)
    self.entry_manopera.grid(row=0, column=3, padx=5, pady=5)

    ttk.Label(frame_edit, text="Sumă Achitată (RON):").grid(
        row=0, column=4, sticky=tk.W, padx=5, pady=5
    )
    self.entry_achitat = ttk.Entry(frame_edit, width=15)
    self.entry_achitat.grid(row=0, column=5, padx=5, pady=5)

    btn_actualizeaza_deviz = ttk.Button(
        frame_edit, text="Actualizează Devizul", command=self.actualizeaza_deviz
    )
    btn_actualizeaza_deviz.grid(row=0, column=6, padx=20, pady=5)

    self.tree_devize.bind("<<TreeviewSelect>>", self.populeaza_campuri_deviz)

  def populeaza_campuri_deviz(self, event):
    selected = self.tree_devize.selection()
    if not selected:
      return
    item = self.tree_devize.item(selected[0])["values"]
    deviz_id = item[0]

    self.db.cursor.execute(
        "SELECT piese_cost, manopera_cost, suma_achitata FROM devize WHERE id = ?",
        (deviz_id,),
    )
    res = self.db.cursor.fetchone()
    if res:
      self.entry_piese.delete(0, tk.END)
      self.entry_piese.insert(0, str(res[0]))
      self.entry_manopera.delete(0, tk.END)
      self.entry_manopera.insert(0, str(res[1]))
      self.entry_achitat.delete(0, tk.END)
      self.entry_achitat.insert(0, str(res[2]))

  def actualizeaza_deviz(self):
    selected = self.tree_devize.selection()
    if not selected:
      messagebox.showwarning(
          "Atenție", "Selectați un deviz din tabel pentru actualizare!"
      )
      return

    deviz_id = self.tree_devize.item(selected[0])["values"][0]

    try:
      piese = float(self.entry_piese.get().strip())
      manopera = float(self.entry_manopera.get().strip())
      achitat = float(self.entry_achitat.get().strip())
    except ValueError:
      messagebox.showerror(
          "Eroare",
          "Valorile introduse pentru costuri și sume trebuie să fie numerice!",
      )
      return

    if piese < 0 or manopera < 0 or achitat < 0:
      messagebox.showerror("Erore", "Valorile nu pot fi negative!")
      return

    self.db.cursor.execute(
        """
            UPDATE devize 
            SET piese_cost = ?, manopera_cost = ?, suma_achitata = ?
            WHERE id = ?
        """,
        (piese, manopera, achitat, deviz_id),
    )
    self.db.conn.commit()

    messagebox.showinfo("Succes", "Devizul a fost actualizat cu succes!")
    self.refresh_all_data()

  # 5. Sincronizarea și reîmprospătarea automată a datelor în interfață
  def refresh_all_data(self):
    for row in self.tree_echipamente.get_children():
      self.tree_echipamente.delete(row)
    for row in self.tree_mentenanta.get_children():
      self.tree_mentenanta.delete(row)
    for row in self.tree_devize.get_children():
      self.tree_devize.delete(row)

    self.db.cursor.execute("SELECT id, nume, serie, locatie FROM echipamente")
    echipamente_list = self.db.cursor.fetchall()
    combo_eq_values = []
    for eq in echipamente_list:
      self.tree_echipamente.insert("", tk.END, values=eq)
      combo_eq_values.append(f"{eq[0]} - {eq[1]} (Serie: {eq[2]})")
    self.combo_eq["values"] = combo_eq_values
    if combo_eq_values:
      self.combo_eq.current(0)
    else:
      self.combo_eq.set("")

    query_ment = """
            SELECT m.id, e.nume, m.tip_revizie, m.data_inceput, m.data_sfarsit, m.status
            FROM mentenanta m
            JOIN echipamente e ON m.echipament_id = e.id
        """
    self.db.cursor.execute(query_ment)
    for row in self.db.cursor.fetchall():
      self.tree_mentenanta.insert("", tk.END, values=row)

    query_devize = """
            SELECT d.id, e.nume, m.tip_revizie, d.piese_cost, d.manopera_cost, 
                   (d.piese_cost + d.manopera_cost) AS total, 
                   d.suma_achitata, 
                   ((d.piese_cost + d.manopera_cost) - d.suma_achitata) AS rest
            FROM devize d
            JOIN mentenanta m ON d.mentenanta_id = m.id
            JOIN echipamente e ON m.echipament_id = e.id
        """
    self.db.cursor.execute(query_devize)
    for row in self.db.cursor.fetchall():
      formatted_row = (
          row[0],
          row[1],
          row[2],
          f"{row[3]:.2f}",
          f"{row[4]:.2f}",
          f"{row[5]:.2f}",
          f"{row[6]:.2f}",
          f"{row[7]:.2f}",
      )
      self.tree_devize.insert("", tk.END, values=formatted_row)


if __name__ == "__main__":
  root = tk.Tk()
  app = CMMSApp(root)
  root.mainloop()