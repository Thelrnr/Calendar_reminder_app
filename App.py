import tkinter as tk
import tkinter.ttk as ttk
import calendar
import datetime
import tkinter.filedialog as filedialog
import csv
import tkinter.messagebox as mb
from dateutil.relativedelta import relativedelta
import uuid
import json
import winsound

class CalendarApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Calendar and Reminder Application")
        self.root.geometry("1000x600") # Wider window for sidebar

        # Theme setup
        self.current_theme = 'light'
        self.setup_themes()

        # Configure root window for better resizing
        self.root.grid_columnconfigure(0, weight=0)  # Sidebar
        self.root.grid_columnconfigure(1, weight=1)  # Calendar
        self.root.grid_columnconfigure(2, weight=1)  # Reminders
        self.root.grid_rowconfigure(0, weight=1)

        # Sidebar for today's reminders
        self.sidebar_frame = ttk.Frame(root, padding=10)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Main frames
        self.calendar_frame = ttk.Frame(root, padding=10)
        self.reminder_frame = ttk.Frame(root, padding=10)
        self.calendar_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.reminder_frame.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)

        self.calendar_grid = None  # Placeholder for future calendar grid widget

        self.year = 2024
        self.month = 7
        self.reminders = {}
        self.current_date = None

        self.load_reminders()  # Load reminders from file on startup

        self.create_sidebar_widgets()
        self.create_reminder_widgets()
        self.create_reminder_display()
        self.create_calendar_widgets()
        self.create_menu()

        self.update_sidebar()
        self.check_reminders()

    def setup_themes(self):
        style = ttk.Style()
        # Light theme
        style.theme_create('playful_light', parent='clam', settings={
            '.': {
                'configure': {
                    'background': '#f9f6ff',
                    'foreground': '#222',
                    'font': ('Comic Sans MS', 10)
                }
            },
            'TButton': {
                'configure': {
                    'background': '#ffe066',
                    'foreground': '#222',
                    'padding': 6,
                    'relief': 'flat',
                },
                'map': {
                    'background': [('active', '#ffd166')],
                }
            },
            'TLabel': {
                'configure': {
                    'background': '#f9f6ff',
                    'foreground': '#222',
                }
            },
            'TFrame': {
                'configure': {
                    'background': '#f9f6ff',
                }
            },
        })
        # Dark theme
        style.theme_create('playful_dark', parent='clam', settings={
            '.': {
                'configure': {
                    'background': '#232946',
                    'foreground': '#eebbc3',
                    'font': ('Comic Sans MS', 10)
                }
            },
            'TButton': {
                'configure': {
                    'background': '#eebbc3',
                    'foreground': '#232946',
                    'padding': 6,
                    'relief': 'flat',
                },
                'map': {
                    'background': [('active', '#ffd166')],
                }
            },
            'TLabel': {
                'configure': {
                    'background': '#232946',
                    'foreground': '#eebbc3',
                }
            },
            'TFrame': {
                'configure': {
                    'background': '#232946',
                }
            },
        })
        style.theme_use('playful_light')

    def toggle_theme(self):
        style = ttk.Style()
        if self.current_theme == 'light':
            style.theme_use('playful_dark')
            self.current_theme = 'dark'
        else:
            style.theme_use('playful_light')
            self.current_theme = 'light'

    def create_sidebar_widgets(self):
        # Search bar
        ttk.Label(self.sidebar_frame, text="🔍 Search Reminders", font=('Arial', 12, 'bold')).pack(pady=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', lambda *args: self.update_search_results())
        search_entry = ttk.Entry(self.sidebar_frame, textvariable=self.search_var)
        search_entry.pack(fill=tk.X, padx=2, pady=(0, 8))

        # Search results frame (scrollable)
        self.search_results_canvas = tk.Canvas(self.sidebar_frame, height=120, borderwidth=0, highlightthickness=0)
        self.search_results_frame = ttk.Frame(self.search_results_canvas)
        self.search_results_scrollbar = ttk.Scrollbar(self.sidebar_frame, orient="vertical", command=self.search_results_canvas.yview)
        self.search_results_canvas.configure(yscrollcommand=self.search_results_scrollbar.set)
        self.search_results_canvas.pack(fill=tk.X, padx=2, pady=(0, 8), side=tk.TOP)
        self.search_results_scrollbar.pack(fill=tk.Y, side=tk.RIGHT, padx=(0, 2))
        self.search_results_canvas.create_window((0, 0), window=self.search_results_frame, anchor="nw")
        self.search_results_frame.bind("<Configure>", lambda e: self.search_results_canvas.configure(scrollregion=self.search_results_canvas.bbox("all")))

        # Today's reminders section
        ttk.Label(self.sidebar_frame, text="⏰ Today's Reminders", font=('Arial', 14, 'bold')).pack(pady=(0, 10))
        self.today_reminders_frame = ttk.Frame(self.sidebar_frame)
        self.today_reminders_frame.pack(fill=tk.BOTH, expand=True)
        self.update_search_results()

    def update_search_results(self):
        # Clear previous search results
        for widget in self.search_results_frame.winfo_children():
            widget.destroy()
        query = self.search_var.get().strip().lower()
        if not query:
            return
        results = []
        for date, reminders in self.reminders.items():
            for reminder in reminders:
                if (query in reminder.get('title', '').lower() or query in reminder.get('desc', '').lower()):
                    results.append((date, reminder))
        if results:
            for date, reminder in sorted(results, key=lambda x: (x[0], x[1].get('time', ''))):
                text = f"{date} {reminder.get('time', 'N/A')}\n{reminder.get('title', '')}"
                btn = ttk.Button(self.search_results_frame, text=text, style="Search.TButton", width=28, command=lambda d=date: self.jump_to_date(d))
                btn.pack(anchor="w", pady=2, fill=tk.X)
        else:
            ttk.Label(self.search_results_frame, text="No results.", font=('Arial', 10, 'italic')).pack(anchor="w")

    def jump_to_date(self, date):
        try:
            dt = datetime.datetime.strptime(date, "%Y-%m-%d")
            self.year = dt.year
            self.month = dt.month
            self.current_date = date
            self.update_calendar()
            self.display_reminders(date)
            self.date_entry.delete(0, tk.END)
            self.date_entry.insert(0, date)
        except Exception as e:
            print(f"Error jumping to date: {e}")

    def update_sidebar(self):
        # Clear previous widgets
        for widget in self.today_reminders_frame.winfo_children():
            widget.destroy()
        today = datetime.date.today().strftime("%Y-%m-%d")
        reminders = self.reminders.get(today, [])
        if reminders:
            reminders_sorted = sorted(reminders, key=lambda r: r.get('time', ''))
            for reminder in reminders_sorted:
                text = f"{reminder.get('time', 'N/A')} - {reminder.get('title', 'N/A')}\n{reminder.get('desc', '')}"
                ttk.Label(self.today_reminders_frame, text="🎈 " + text, justify=tk.LEFT, wraplength=180).pack(anchor="w", pady=4, fill=tk.X)
        else:
            ttk.Label(self.today_reminders_frame, text="No reminders for today.", font=('Arial', 10, 'italic')).pack(anchor="w")

    def create_calendar_widgets(self):
        # Remove old calendar grid and navigation
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()

        # Calendar title
        self.calendar_title_label = ttk.Label(self.calendar_frame, text="🗓️ Calendar", font=('Arial', 18, 'bold'))
        self.calendar_title_label.pack(pady=(10, 20))

        # Digital clock-style dials (vertical stack)
        self.dials_frame = ttk.Frame(self.calendar_frame)
        self.dials_frame.pack(pady=10)

        import calendar
        now = datetime.datetime.now()
        self.lockdial_year = now.year
        self.lockdial_month = now.month
        self.lockdial_day = now.day

        # Helper to get max day for current year/month
        def get_max_day(year, month):
            return calendar.monthrange(year, month)[1]

        def update_date_display():
            self.year_label.config(text=f"{self.lockdial_year:04d}")
            self.month_label.config(text=f"{self.lockdial_month:02d}")
            self.day_label.config(text=f"{self.lockdial_day:02d}")
            # Clamp day if needed
            max_day = get_max_day(self.lockdial_year, self.lockdial_month)
            if self.lockdial_day > max_day:
                self.lockdial_day = max_day
                self.day_label.config(text=f"{self.lockdial_day:02d}")
            # Update current date and reminders
            self.year = self.lockdial_year
            self.month = self.lockdial_month
            self.current_date = f"{self.lockdial_year}-{self.lockdial_month:02d}-{self.lockdial_day:02d}"
            self.date_entry.delete(0, tk.END)
            self.date_entry.insert(0, self.current_date)
            self.display_reminders(self.current_date)

        # Year controls
        year_frame = ttk.Frame(self.dials_frame)
        year_frame.pack(pady=8)
        year_up = ttk.Button(year_frame, text="▲", width=2, command=lambda: self.change_year(1, update_date_display), style="Small.TButton")
        year_up.pack()
        self.year_label = ttk.Label(year_frame, text=f"{self.lockdial_year:04d}", font=('Courier', 44, 'bold'), width=7, anchor="center")
        self.year_label.pack()
        year_down = ttk.Button(year_frame, text="▼", width=2, command=lambda: self.change_year(-1, update_date_display), style="Small.TButton")
        year_down.pack()

        # Month controls
        month_frame = ttk.Frame(self.dials_frame)
        month_frame.pack(pady=8)
        month_up = ttk.Button(month_frame, text="▲", width=2, command=lambda: self.change_month(1, update_date_display), style="Small.TButton")
        month_up.pack()
        self.month_label = ttk.Label(month_frame, text=f"{self.lockdial_month:02d}", font=('Courier', 44, 'bold'), width=5, anchor="center")
        self.month_label.pack()
        month_down = ttk.Button(month_frame, text="▼", width=2, command=lambda: self.change_month(-1, update_date_display), style="Small.TButton")
        month_down.pack()

        # Day controls
        day_frame = ttk.Frame(self.dials_frame)
        day_frame.pack(pady=8)
        day_up = ttk.Button(day_frame, text="▲", width=2, command=lambda: self.change_day(1, update_date_display), style="Small.TButton")
        day_up.pack()
        self.day_label = ttk.Label(day_frame, text=f"{self.lockdial_day:02d}", font=('Courier', 44, 'bold'), width=5, anchor="center")
        self.day_label.pack()
        day_down = ttk.Button(day_frame, text="▼", width=2, command=lambda: self.change_day(-1, update_date_display), style="Small.TButton")
        day_down.pack()

        # Style for smaller buttons
        style = ttk.Style()
        style.configure("Small.TButton", font=("Arial", 12))

        # Initial display
        update_date_display()

    def change_year(self, delta, update_callback):
        self.lockdial_year += delta
        if self.lockdial_year < 1900:
            self.lockdial_year = 1900
        if self.lockdial_year > 2100:
            self.lockdial_year = 2100
        update_callback()

    def change_month(self, delta, update_callback):
        self.lockdial_month += delta
        if self.lockdial_month < 1:
            self.lockdial_month = 12
            self.lockdial_year -= 1
        elif self.lockdial_month > 12:
            self.lockdial_month = 1
            self.lockdial_year += 1
        if self.lockdial_year < 1900:
            self.lockdial_year = 1900
            self.lockdial_month = 1
        if self.lockdial_year > 2100:
            self.lockdial_year = 2100
            self.lockdial_month = 12
        update_callback()

    def change_day(self, delta, update_callback):
        import calendar
        max_day = calendar.monthrange(self.lockdial_year, self.lockdial_month)[1]
        self.lockdial_day += delta
        if self.lockdial_day < 1:
            self.lockdial_month -= 1
            if self.lockdial_month < 1:
                self.lockdial_month = 12
                self.lockdial_year -= 1
            self.lockdial_day = calendar.monthrange(self.lockdial_year, self.lockdial_month)[1]
        elif self.lockdial_day > max_day:
            self.lockdial_day = 1
            self.lockdial_month += 1
            if self.lockdial_month > 12:
                self.lockdial_month = 1
                self.lockdial_year += 1
        if self.lockdial_year < 1900:
            self.lockdial_year = 1900
            self.lockdial_month = 1
            self.lockdial_day = 1
        if self.lockdial_year > 2100:
            self.lockdial_year = 2100
            self.lockdial_month = 12
            self.lockdial_day = calendar.monthrange(self.lockdial_year, self.lockdial_month)[1]
        update_callback()

    def create_reminder_widgets(self):
        # Frame for reminder input fields with styling
        input_frame = ttk.Frame(self.reminder_frame)
        input_frame.pack(pady=10, fill=tk.X)

        # Configure grid weights for input frame columns for better layout
        input_frame.grid_columnconfigure(0, weight=0) # Labels column
        input_frame.grid_columnconfigure(1, weight=1) # Entry fields column

        ttk.Label(input_frame, text="📅 Date (YYYY-MM-DD):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.date_entry = ttk.Entry(input_frame)
        self.date_entry.grid(row=0, column=1, padx=5, pady=5, sticky="we")

        ttk.Label(input_frame, text="⏰ Time (HH:MM):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.time_entry = ttk.Entry(input_frame)
        self.time_entry.grid(row=1, column=1, padx=5, pady=5, sticky="we")

        ttk.Label(input_frame, text="🎉 Title:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.title_entry = ttk.Entry(input_frame)
        self.title_entry.grid(row=2, column=1, padx=5, pady=5, sticky="we")

        ttk.Label(input_frame, text="📝 Description:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.desc_entry = ttk.Entry(input_frame)
        self.desc_entry.grid(row=3, column=1, padx=5, pady=5, sticky="we")

        ttk.Label(input_frame, text="🔁 Recurrence (daily, weekly, monthly):").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.recurrence_entry = ttk.Entry(input_frame)
        self.recurrence_entry.grid(row=4, column=1, padx=5, pady=5, sticky="we")

        ttk.Label(input_frame, text="🏁 End Date (YYYY-MM-DD):").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.end_date_entry = ttk.Entry(input_frame)
        self.end_date_entry.grid(row=5, column=1, padx=5, pady=5, sticky="we")

        ttk.Label(input_frame, text="🏷️ Tags (comma-separated):").grid(row=6, column=0, padx=5, pady=5, sticky="w")
        self.tags_entry = ttk.Entry(input_frame)
        self.tags_entry.grid(row=6, column=1, padx=5, pady=5, sticky="we")

        self.add_reminder_button = ttk.Button(self.reminder_frame, text="➕ Add Reminder", command=self.add_reminder)
        self.add_reminder_button.pack(pady=10)

        self.editing_reminder_id = None

    def create_reminder_display(self):
        ttk.Label(self.reminder_frame, text="📋 Reminders:", font=('Arial', 12, 'underline')).pack(pady=(10, 5), anchor="w")
        # Use a ScrolledText widget or a Frame with a Scrollbar for potentially many reminders
        # For simplicity here, we'll continue using a Frame and pack items into it
        self.reminder_display_frame = ttk.Frame(self.reminder_frame)
        self.reminder_display_frame.pack(fill=tk.BOTH, expand=True)

    def create_menu(self):
        menubar = tk.Menu(self.root)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Export Reminders", command=self.export_reminders)
        filemenu.add_command(label="Import Reminders", command=self.import_reminders)
        menubar.add_cascade(label="File", menu=filemenu)
        # Theme toggle
        thememenu = tk.Menu(menubar, tearoff=0)
        thememenu.add_command(label="Toggle Light/Dark Theme", command=self.toggle_theme)
        menubar.add_cascade(label="Theme", menu=thememenu)
        self.root.config(menu=menubar)

    def update_calendar(self):
        self.month_year_label.config(text=f"{calendar.month_name[self.month]} {self.year}")
        cal_content = calendar.month(self.year, self.month)
        self.calendar_grid.config(state='normal')
        self.calendar_grid.delete(1.0, tk.END)
        self.calendar_grid.insert(tk.END, cal_content)
        self.highlight_calendar_dates() # Add highlighting
        self.calendar_grid.config(state='disabled')

    def highlight_calendar_dates(self):
        """Highlights weekdays, weekends, and selected date in the calendar."""
        self.calendar_grid.tag_configure("weekday", foreground="black")
        self.calendar_grid.tag_configure("weekend", foreground="red")
        self.calendar_grid.tag_configure("selected", background="yellow", foreground="blue")
        self.calendar_grid.tag_configure("reminder_date", background="lightblue") # Highlight dates with reminders

        cal_lines = self.calendar_grid.get(1.0, tk.END).split('\n')
        # Skip header lines (month/year and weekday names)
        if len(cal_lines) > 2:
            # Tag weekday names
            weekday_names_line = cal_lines[1]
            for i, day_name in enumerate(['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']):
                start_index = weekday_names_line.find(day_name)
                if start_index != -1:
                     # Apply weekday tag
                     self.calendar_grid.tag_add("weekday", f"2.{start_index}", f"2.{start_index + len(day_name)}")


            # Tag days in the grid
            for line_num in range(3, len(cal_lines) + 1): # Start from the line with days
                week_line = cal_lines[line_num - 1]
                day_start_index = 0
                for i in range(7): # Iterate through days of the week
                    # Find the start index of the number for the current day
                    # Handle potential spaces before single-digit days
                    day_str = week_line[day_start_index:day_start_index + 3].strip()
                    try:
                         day = int(day_str)
                         current_date_str = f"{self.year}-{self.month:02d}-{day:02d}"

                         # Check if this date has reminders
                         if current_date_str in self.reminders and self.reminders[current_date_str]:
                            self.calendar_grid.tag_add("reminder_date", f"{line_num}.{day_start_index}", f"{line_num}.{day_start_index + len(day_str)}")


                         # Check if this is the selected date
                         if self.current_date == current_date_str:
                             self.calendar_grid.tag_add("selected", f"{line_num}.{day_start_index}", f"{line_num}.{day_start_index + len(day_str)}")


                         # Check if weekend (Sa or Su column)
                         if i >= 5: # Saturday or Sunday columns
                             self.calendar_grid.tag_add("weekend", f"{line_num}.{day_start_index}", f"{line_num}.{day_start_index + len(day_str)}")
                         else: # Weekday columns
                             self.calendar_grid.tag_add("weekday", f"{line_num}.{day_start_index}", f"{line_num}.{day_start_index + len(day_str)}")


                    except ValueError:
                         # Not a day number (e.g., empty space from previous/next month)
                         pass
                    day_start_index += 3 # Move to the next day's position (assuming 3 chars per day slot)


    def prev_month(self):
        self.month -= 1
        if self.month < 1:
            self.month = 12
            self.year -= 1
        self.update_calendar()
        # No need to auto-display reminders for the previous month unless a date was already selected
        # if self.current_date:
        #      self.display_reminders(self.current_date)


    def next_month(self):
        self.month += 1
        if self.month > 12:
            self.month = 1
            self.year += 1
        self.update_calendar()
        # No need to auto-display reminders for the next month unless a date was already selected
        # if self.current_date:
        #      self.display_reminders(self.current_date)


    def date_selected(self, event):
        """Handles date selection from the calendar grid."""
        try:
            index = self.calendar_grid.index("@%s,%s" % (event.x, event.y))
            line, col = map(int, index.split("."))
            # Extract the day number from the clicked position
            day_str = self.calendar_grid.get(f"{line}.{col}", f"{line}.{col + 2}").strip()
            try:
                day = int(day_str)
                # Construct the full date string
                selected_date_str = f"{self.year}-{self.month:02d}-{day:02d}"
                # Validate the date
                datetime.datetime.strptime(selected_date_str, "%Y-%m-%d")
                self.current_date = selected_date_str
                self.display_reminders(self.current_date)
                self.date_entry.delete(0, tk.END)
                self.date_entry.insert(0, self.current_date) # Populate date entry
                self.update_calendar() # Re-highlight the selected date
            except ValueError:
                # Click was not on a valid day number or date is invalid for the month
                pass
        except tk.TclError:
            # Handle cases where the click is outside the text area
            pass


    def display_reminders(self, date):
        """Displays reminders for the given date with edit and delete buttons."""
        # Clear the current display frame
        for widget in self.reminder_display_frame.winfo_children():
            widget.destroy()

        ttk.Label(self.reminder_display_frame, text=f"📅 Reminders for {date}:", font=('Arial', 10, 'bold')).pack(pady=(0, 5), anchor="w")


        if date in self.reminders and self.reminders[date]:
            reminders_list = sorted(self.reminders[date], key=lambda r: r['time']) # Sort by time
            for i, reminder in enumerate(reminders_list):
                # Create a frame for each reminder item
                reminder_item_frame = ttk.Frame(self.reminder_display_frame)
                reminder_item_frame.pack(fill=tk.X, pady=2)
                reminder_item_frame.grid_columnconfigure(0, weight=1) # Text label column

                # Reminder details label
                reminder_text = f"Time: {reminder.get('time', 'N/A')}, Title: {reminder.get('title', 'N/A')}\nDesc: {reminder.get('desc', 'N/A')}\nRecurrence: {reminder.get('recurrence', 'None')}"
                if reminder.get('end_date', ''):
                    reminder_text += f"\nEnd Date: {reminder.get('end_date', '')}"
                if reminder.get('tags', []):
                    reminder_text += f"\nTags: {', '.join(reminder.get('tags', []))}"
                ttk.Label(reminder_item_frame, text=reminder_text, justify=tk.LEFT, wraplength=300, font=('Arial', 9)).grid(row=0, column=0, sticky="w")

                # Button frame for edit/delete
                button_frame = ttk.Frame(reminder_item_frame)
                button_frame.grid(row=0, column=1, sticky="e")

                # Add Edit button
                edit_button = ttk.Button(button_frame, text="✏️ Edit", command=lambda r_id=reminder['id']: self.edit_reminder(date, r_id))
                edit_button.pack(side=tk.LEFT, padx=2)

                # Add Delete button
                delete_button = ttk.Button(button_frame, text="🗑️ Delete", command=lambda r_id=reminder['id']: self.delete_reminder(date, r_id))
                delete_button.pack(side=tk.LEFT)

        else:
            ttk.Label(self.reminder_display_frame, text="No reminders for this date.", font=('Arial', 10, 'italic')).pack()

    def add_reminder(self):
        date = self.date_entry.get()
        time = self.time_entry.get()
        title = self.title_entry.get()
        desc = self.desc_entry.get()
        recurrence = self.recurrence_entry.get().lower()
        end_date = self.end_date_entry.get().strip()
        tags = [t.strip() for t in self.tags_entry.get().split(',') if t.strip()]

        if not date or not title:
            mb.showerror("Input Error", "Date and Title are required.")
            return

        try:
            datetime.datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            mb.showerror("Input Error", "Invalid date format. Please use YYYY-MM-DD.")
            return

        if time:
            try:
                datetime.datetime.strptime(time, "%H:%M")
            except ValueError:
                mb.showerror("Input Error", "Invalid time format. Please use HH:MM.")
                return

        valid_recurrences = ["", "daily", "weekly", "monthly"]
        if recurrence not in valid_recurrences:
             mb.showerror("Input Error", "Invalid recurrence. Please use daily, weekly, or monthly.")
             return

        if end_date:
            try:
                datetime.datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                mb.showerror("Input Error", "Invalid end date format. Please use YYYY-MM-DD.")
                return

        if self.editing_reminder_id:
            # Find the reminder across all dates (in case the date was changed during edit)
            found_reminder = None
            original_date = None
            for d, reminders_list in list(self.reminders.items()): # Iterate over a copy
                 for i, reminder in enumerate(reminders_list):
                     if reminder['id'] == self.editing_reminder_id:
                         found_reminder = reminder
                         original_date = d
                         break
                 if found_reminder:
                     break

            if found_reminder:
                # If the date changed, remove from old date's list
                if original_date != date:
                     self.reminders[original_date] = [r for r in self.reminders[original_date] if r['id'] != self.editing_reminder_id]
                     if not self.reminders[original_date]:
                         del self.reminders[original_date]
                     # Add to new date's list
                     if date not in self.reminders:
                         self.reminders[date] = []
                     self.reminders[date].append(found_reminder)

                # Update the reminder details
                found_reminder.update({
                    'date': date, # Update date in reminder object as well
                    'time': time,
                    'title': title,
                    'desc': desc,
                    'recurrence': recurrence,
                    'end_date': end_date,
                    'tags': tags
                })
                mb.showinfo("Success", "Reminder updated successfully.")
            else:
                 mb.showerror("Error", "Could not find reminder to update.")

            self.editing_reminder_id = None
            self.add_reminder_button.config(text="➕ Add Reminder") # No bg for ttk
            self.save_reminders()
            self.update_sidebar()
            self.update_search_results()
        else:
            new_reminder = {
                'id': str(uuid.uuid4()),
                'date': date,
                'time': time,
                'title': title,
                'desc': desc,
                'recurrence': recurrence,
                'end_date': end_date,
                'tags': tags
            }

            if date not in self.reminders:
                self.reminders[date] = []

            self.reminders[date].append(new_reminder)
            mb.showinfo("Success", "Reminder added successfully.")
            self.save_reminders()
            self.update_sidebar()
            self.update_search_results()

        # Clear input fields
        self.date_entry.delete(0, tk.END)
        self.time_entry.delete(0, tk.END)
        self.title_entry.delete(0, tk.END)
        self.desc_entry.delete(0, tk.END)
        self.recurrence_entry.delete(0, tk.END)
        self.end_date_entry.delete(0, tk.END)
        self.tags_entry.delete(0, tk.END)

        # Update display for the date where the reminder was added/updated
        self.current_date = date # Set current date to the modified date
        self.display_reminders(self.current_date)
        self.update_calendar() # Update calendar highlighting


    def edit_reminder(self, date, reminder_id):
        """Populates input fields with reminder details for editing."""
        if date in self.reminders:
            for reminder in self.reminders[date]:
                if reminder['id'] == reminder_id:
                    # Populate input fields
                    self.date_entry.delete(0, tk.END)
                    self.date_entry.insert(0, reminder['date'])
                    self.time_entry.delete(0, tk.END)
                    self.time_entry.insert(0, reminder['time'])
                    self.title_entry.delete(0, tk.END)
                    self.title_entry.insert(0, reminder['title'])
                    self.desc_entry.delete(0, tk.END)
                    self.desc_entry.insert(0, reminder['desc'])
                    self.recurrence_entry.delete(0, tk.END)
                    self.recurrence_entry.insert(0, reminder['recurrence'])
                    self.end_date_entry.delete(0, tk.END)
                    self.end_date_entry.insert(0, reminder.get('end_date', ''))
                    self.tags_entry.delete(0, tk.END)
                    self.tags_entry.insert(0, ', '.join(reminder.get('tags', [])))

                    self.editing_reminder_id = reminder_id
                    self.add_reminder_button.config(text="✏️ Update Reminder") # No bg for ttk
                    break

    def delete_reminder(self, date, reminder_id):
        """Deletes a reminder based on its ID."""
        if date in self.reminders:
            # Find the index of the reminder to delete
            index_to_delete = -1
            for i, reminder in enumerate(self.reminders[date]):
                 if reminder['id'] == reminder_id:
                     index_to_delete = i
                     break

            if index_to_delete != -1:
                 del self.reminders[date][index_to_delete]
                 if not self.reminders[date]:
                     del self.reminders[date]
                 self.save_reminders()
                 self.update_sidebar()
                 self.update_search_results()
                 mb.showinfo("Success", "Reminder deleted successfully.")
                 # Update the display for the current date
                 if self.current_date:
                    self.display_reminders(self.current_date)
                 self.update_calendar() # Update calendar highlighting
            else:
                 mb.showerror("Error", "Could not find reminder to delete.")


    def calculate_next_occurrence(self, original_date_str, recurrence, current_date):
        """Calculates the next occurrence date for a recurring reminder."""
        try:
            original_date = datetime.datetime.strptime(original_date_str, "%Y-%m-%d").date()
        except ValueError:
            return None

        if recurrence == "daily":
            if original_date <= current_date:
                 return current_date + datetime.timedelta(days=1)
            else:
                 return original_date
        elif recurrence == "weekly":
            days_difference = (original_date.weekday() - current_date.weekday() + 7) % 7
            if days_difference == 0 and original_date <= current_date:
                 days_difference = 7
            elif days_difference == 0 and original_date > current_date:
                 days_difference = 0
            return current_date + datetime.timedelta(days=days_difference)

        elif recurrence == "monthly":
            next_date = current_date
            while next_date.day != original_date.day or next_date < original_date:
                 next_date += relativedelta(months=1)
            if next_date < current_date:
                 next_date += relativedelta(months=1)
            return next_date
        else:
            return None

    def check_reminders(self):
        now = datetime.datetime.now()
        current_date = now.date()
        current_time_str = now.strftime("%H:%M")

        current_date_str = current_date.strftime("%Y-%m-%d")
        if current_date_str in self.reminders:
            reminders_today = self.reminders[current_date_str]
            for reminder in reminders_today:
                if reminder.get('recurrence', '') == "" and reminder.get('time', '') == current_time_str: # Use .get with default
                    # Play sound notification
                    winsound.Beep(1000, 500)  # 1000 Hz, 500 ms
                    print(f"Notification: Reminder: {reminder.get('title', 'N/A')} at {reminder.get('time', 'N/A')}") # Use .get

        for date, reminders_list in self.reminders.items():
            for reminder in reminders_list:
                recurrence = reminder.get('recurrence', '')
                if recurrence in ["daily", "weekly", "monthly"]:
                    end_date_str = reminder.get('end_date', '')
                    if end_date_str:
                        try:
                            end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").date()
                        except ValueError:
                            end_date = None
                    else:
                        end_date = None
                    next_occurrence_date = self.calculate_next_occurrence(reminder.get('date', ''), recurrence, current_date) # Use .get

                    # Only trigger if current_date <= end_date (or no end_date)
                    if next_occurrence_date and next_occurrence_date == current_date and reminder.get('time', '') == current_time_str:
                        if not end_date or current_date <= end_date:
                            # Play sound notification
                            winsound.Beep(1200, 500)  # 1200 Hz, 500 ms
                            print(f"Notification: Recurring Reminder: {reminder.get('title', 'N/A')} at {reminder.get('time', 'N/A')} (originally on {reminder.get('date', 'N/A')})") # Use .get

        self.root.after(60000, self.check_reminders)

    def export_reminders(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if not file_path:
            return

        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Date", "Time", "Title", "Description", "Recurrence"])

                for date, reminders_list in self.reminders.items():
                    for reminder in reminders_list:
                         writer.writerow([
                             reminder.get('id', ''),
                             reminder.get('date', ''),
                             reminder.get('time', ''),
                             reminder.get('title', ''),
                             reminder.get('desc', ''),
                             reminder.get('recurrence', '')
                         ])


            print(f"Reminders exported to {file_path}")
        except Exception as e:
            print(f"Error exporting reminders: {e}")

    def import_reminders(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if not file_path:
            return

        try:
            with open(file_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)

                try:
                     id_col = header.index("ID")
                     date_col = header.index("Date")
                     time_col = header.index("Time")
                     title_col = header.index("Title")
                     desc_col = header.index("Description")
                     recurrence_col = header.index("Recurrence")
                except ValueError:
                     id_col = -1
                     date_col = 0
                     time_col = 1
                     title_col = 2
                     desc_col = 3
                     recurrence_col = 4

                imported_count = 0
                for row in reader:
                    # Check if row has enough columns based on the highest index
                    if len(row) > max(date_col, time_col, title_col, desc_col, recurrence_col) and (id_col == -1 or len(row) > id_col):
                        reminder_id = row[id_col] if id_col != -1 and len(row) > id_col else str(uuid.uuid4())
                        try:
                            date = row[date_col] if len(row) > date_col else ""
                            time = row[time_col] if len(row) > time_col else ""
                            title = row[title_col] if len(row) > title_col else ""
                            desc = row[desc_col] if len(row) > desc_col else ""
                            recurrence = row[recurrence_col] if len(row) > recurrence_col else ""


                            # Basic validation for imported data
                            datetime.datetime.strptime(date, "%Y-%m-%d")
                            if time:
                                 datetime.datetime.strptime(time, "%H:%M")
                            valid_recurrences = ["", "daily", "weekly", "monthly"]
                            if recurrence not in valid_recurrences:
                                 recurrence = ""

                            new_reminder = {
                                'id': reminder_id,
                                'date': date,
                                'time': time,
                                'title': title,
                                'desc': desc,
                                'recurrence': recurrence
                            }

                            if date not in self.reminders:
                                self.reminders[date] = []

                            if reminder_id not in [r.get('id', '') for r in self.reminders[date]]: # Use .get for ID check
                                 self.reminders[date].append(new_reminder)
                                 imported_count += 1
                            else:
                                 print(f"Skipping duplicate reminder with ID: {reminder_id}")

                        except ValueError:
                            print(f"Skipping row with invalid date or time format: {row}")
                        except IndexError:
                             print(f"Skipping invalid row format: {row}")
                    else:
                        print(f"Skipping invalid row length: {row}")


            print(f"Successfully imported {imported_count} reminders from {file_path}")
            self.save_reminders()
            self.update_sidebar()
            self.update_search_results()
            if self.current_date:
                self.display_reminders(self.current_date)
            self.update_calendar() # Update calendar highlighting


        except FileNotFoundError:
            print(f"Error: File not found at {file_path}")
        except Exception as e:
            print(f"Error importing reminders: {e}")

    def save_reminders(self):
        try:
            with open("reminders.json", "w", encoding="utf-8") as f:
                json.dump(self.reminders, f, indent=2)
        except Exception as e:
            print(f"Error saving reminders: {e}")

    def load_reminders(self):
        try:
            with open("reminders.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                # Convert keys to str and values to list of dicts
                self.reminders = {str(k): v for k, v in data.items()}
        except FileNotFoundError:
            self.reminders = {}
        except Exception as e:
            print(f"Error loading reminders: {e}")
            self.reminders = {}


# Assuming notify_reminder is defined elsewhere, e.g.:
# def notify_reminder(message):
#     mb.showinfo("Reminder", message)


if __name__ == '__main__':
    root = tk.Tk()
    app = CalendarApp(root)
    print("Styling and layout improvements applied. - BABA ")
    root.mainloop()
