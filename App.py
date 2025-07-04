import tkinter as tk
import calendar
import datetime
import tkinter.filedialog as filedialog
import csv
import tkinter.messagebox as mb
from dateutil.relativedelta import relativedelta
import uuid

class CalendarApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Calendar and Reminder Application")
        self.root.geometry("800x600") # Set a default window size

        # Configure root window for better resizing
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # Create frames with some styling
        self.calendar_frame = tk.Frame(root, padx=10, pady=10, bg='#f0f0f0', relief=tk.GROOVE, borderwidth=2)
        self.reminder_frame = tk.Frame(root, padx=10, pady=10, bg='#e0e0e0', relief=tk.GROOVE, borderwidth=2)

        # Use grid layout for the main frames for better responsiveness
        self.calendar_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.reminder_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)


        self.year = 2024
        self.month = 7

        self.reminders = {}
        self.current_date = None

        self.create_calendar_widgets()
        self.create_reminder_widgets()
        self.create_reminder_display()
        self.create_menu()

        self.check_reminders()

    def create_calendar_widgets(self):
        # Month and Year Navigation frame with styling
        nav_frame = tk.Frame(self.calendar_frame, bg='#f0f0f0')
        nav_frame.pack(pady=10)

        self.prev_month_button = tk.Button(nav_frame, text="<", command=self.prev_month, font=('Arial', 10), bg='#cccccc')
        self.prev_month_button.pack(side=tk.LEFT)

        self.month_year_label = tk.Label(nav_frame, text="", font=('Arial', 16, 'bold'), bg='#f0f0f0')
        self.month_year_label.pack(side=tk.LEFT, padx=20)

        self.next_month_button = tk.Button(nav_frame, text=">", command=self.next_month, font=('Arial', 10), bg='#cccccc')
        self.next_month_button.pack(side=tk.LEFT)

        # Calendar Grid with styling
        self.calendar_grid = tk.Text(self.calendar_frame, height=10, width=30, font=('Courier New', 12), state='disabled', bg='#ffffff', fg='#333333')
        self.calendar_grid.pack(fill=tk.BOTH, expand=True)

        self.update_calendar()
        self.calendar_grid.bind("<ButtonRelease-1>", self.date_selected)


    def create_reminder_widgets(self):
        # Frame for reminder input fields with styling
        input_frame = tk.Frame(self.reminder_frame, bg='#e0e0e0')
        input_frame.pack(pady=10, fill=tk.X)

        # Configure grid weights for input frame columns for better layout
        input_frame.grid_columnconfigure(0, weight=0) # Labels column
        input_frame.grid_columnconfigure(1, weight=1) # Entry fields column


        tk.Label(input_frame, text="Date (YYYY-MM-DD):", font=('Arial', 10), bg='#e0e0e0').grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.date_entry = tk.Entry(input_frame, font=('Arial', 10))
        self.date_entry.grid(row=0, column=1, padx=5, pady=5, sticky="we")

        tk.Label(input_frame, text="Time (HH:MM):", font=('Arial', 10), bg='#e0e0e0').grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.time_entry = tk.Entry(input_frame, font=('Arial', 10))
        self.time_entry.grid(row=1, column=1, padx=5, pady=5, sticky="we")

        tk.Label(input_frame, text="Title:", font=('Arial', 10), bg='#e0e0e0').grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.title_entry = tk.Entry(input_frame, font=('Arial', 10))
        self.title_entry.grid(row=2, column=1, padx=5, pady=5, sticky="we")

        tk.Label(input_frame, text="Description:", font=('Arial', 10), bg='#e0e0e0').grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.desc_entry = tk.Entry(input_frame, font=('Arial', 10))
        self.desc_entry.grid(row=3, column=1, padx=5, pady=5, sticky="we")

        tk.Label(input_frame, text="Recurrence (daily, weekly, monthly):", font=('Arial', 10), bg='#e0e0e0').grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.recurrence_entry = tk.Entry(input_frame, font=('Arial', 10))
        self.recurrence_entry.grid(row=4, column=1, padx=5, pady=5, sticky="we")

        self.add_reminder_button = tk.Button(self.reminder_frame, text="Add Reminder", command=self.add_reminder, font=('Arial', 10, 'bold'), bg='#a0a0ff', fg='#ffffff')
        self.add_reminder_button.pack(pady=10)

        self.editing_reminder_id = None

    def create_reminder_display(self):
        tk.Label(self.reminder_frame, text="Reminders:", font=('Arial', 12, 'underline'), bg='#e0e0e0').pack(pady=(10, 5), anchor="w")
        # Use a ScrolledText widget or a Frame with a Scrollbar for potentially many reminders
        # For simplicity here, we'll continue using a Frame and pack items into it
        self.reminder_display_frame = tk.Frame(self.reminder_frame, bg='#d0d0d0', relief=tk.SUNKEN, borderwidth=1, padx=5, pady=5)
        self.reminder_display_frame.pack(fill=tk.BOTH, expand=True)


    def create_menu(self):
        menubar = tk.Menu(self.root)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Export Reminders", command=self.export_reminders)
        filemenu.add_command(label="Import Reminders", command=self.import_reminders)
        menubar.add_cascade(label="File", menu=filemenu)
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

        tk.Label(self.reminder_display_frame, text=f"Reminders for {date}:", font=('Arial', 10, 'bold'), bg='#d0d0d0').pack(pady=(0, 5), anchor="w")


        if date in self.reminders and self.reminders[date]:
            reminders_list = sorted(self.reminders[date], key=lambda r: r['time']) # Sort by time
            for i, reminder in enumerate(reminders_list):
                # Create a frame for each reminder item
                reminder_item_frame = tk.Frame(self.reminder_display_frame, bg='#ffffff', relief=tk.FLAT, borderwidth=1, padx=5, pady=5)
                reminder_item_frame.pack(fill=tk.X, pady=2)
                reminder_item_frame.grid_columnconfigure(0, weight=1) # Text label column

                # Reminder details label
                reminder_text = f"Time: {reminder.get('time', 'N/A')}, Title: {reminder.get('title', 'N/A')}\nDesc: {reminder.get('desc', 'N/A')}\nRecurrence: {reminder.get('recurrence', 'None')}"
                tk.Label(reminder_item_frame, text=reminder_text, justify=tk.LEFT, wraplength=300, font=('Arial', 9), bg='#ffffff').grid(row=0, column=0, sticky="w")

                # Button frame for edit/delete
                button_frame = tk.Frame(reminder_item_frame, bg='#ffffff')
                button_frame.grid(row=0, column=1, sticky="e")

                # Add Edit button
                edit_button = tk.Button(button_frame, text="Edit", font=('Arial', 8), bg='#ffffa0', command=lambda r_id=reminder['id']: self.edit_reminder(date, r_id))
                edit_button.pack(side=tk.LEFT, padx=2)

                # Add Delete button
                delete_button = tk.Button(button_frame, text="Delete", font=('Arial', 8), bg='#ffb0b0', command=lambda r_id=reminder['id']: self.delete_reminder(date, r_id))
                delete_button.pack(side=tk.LEFT)

        else:
            tk.Label(self.reminder_display_frame, text="No reminders for this date.", font=('Arial', 10, 'italic'), bg='#d0d0d0').pack()

    def add_reminder(self):
        date = self.date_entry.get()
        time = self.time_entry.get()
        title = self.title_entry.get()
        desc = self.desc_entry.get()
        recurrence = self.recurrence_entry.get().lower()

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
                    'recurrence': recurrence
                })
                mb.showinfo("Success", "Reminder updated successfully.")
            else:
                 mb.showerror("Error", "Could not find reminder to update.")

            self.editing_reminder_id = None
            self.add_reminder_button.config(text="Add Reminder", bg='#a0a0ff')
        else:
            new_reminder = {
                'id': str(uuid.uuid4()),
                'date': date,
                'time': time,
                'title': title,
                'desc': desc,
                'recurrence': recurrence
            }

            if date not in self.reminders:
                self.reminders[date] = []

            self.reminders[date].append(new_reminder)
            mb.showinfo("Success", "Reminder added successfully.")


        # Clear input fields
        self.date_entry.delete(0, tk.END)
        self.time_entry.delete(0, tk.END)
        self.title_entry.delete(0, tk.END)
        self.desc_entry.delete(0, tk.END)
        self.recurrence_entry.delete(0, tk.END)

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

                    self.editing_reminder_id = reminder_id
                    self.add_reminder_button.config(text="Update Reminder", bg='#a0ffa0') # Change button text and color
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
                 # If no reminders left for the date, remove the date entry
                 if not self.reminders[date]:
                     del self.reminders[date]

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
                    # Assuming notify_reminder is available globally or passed
                    # notify_reminder(f"Reminder: {reminder['title']} at {reminder['time']}")
                    print(f"Notification: Reminder: {reminder.get('title', 'N/A')} at {reminder.get('time', 'N/A')}") # Use .get

        for date, reminders_list in self.reminders.items():
            for reminder in reminders_list:
                recurrence = reminder.get('recurrence', '')
                if recurrence in ["daily", "weekly", "monthly"]:
                    next_occurrence_date = self.calculate_next_occurrence(reminder.get('date', ''), recurrence, current_date) # Use .get

                    if next_occurrence_date and next_occurrence_date == current_date and reminder.get('time', '') == current_time_str: # Use .get
                         # Assuming notify_reminder is available globally or passed
                         # notify_reminder(f"Recurring Reminder: {reminder['title']} at {reminder['time']}")
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

            if self.current_date:
                self.display_reminders(self.current_date)
            self.update_calendar() # Update calendar highlighting


        except FileNotFoundError:
            print(f"Error: File not found at {file_path}")
        except Exception as e:
            print(f"Error importing reminders: {e}")


# Assuming notify_reminder is defined elsewhere, e.g.:
# def notify_reminder(message):
#     mb.showinfo("Reminder", message)


if __name__ == '__main__':
    root = tk.Tk()
    app = CalendarApp(root)
    print("Styling and layout improvements applied.")
