# Student Management System (Tkinter)

A simple GUI to **Add**, **View**, **Update**, and **Delete** student records.

## How to Run

```bash
python student_management.py
```

*(Python 3.x required. Tkinter is included with standard Python.)*

## What Each Command/Part Does

| Command / Code | Explanation |
|----------------|-------------|
| `import tkinter as tk` | Import the Tkinter library for GUI (windows, buttons, etc.) |
| `from tkinter import ttk, messagebox` | Import themed widgets (ttk) and pop-up message boxes |
| `root = tk.Tk()` | Create the main application window |
| `root.title("...")` | Set the window title bar text |
| `root.geometry("700x500")` | Set window width and height in pixels |
| `ttk.Label(frame, text="Name:")` | Create a label (non-editable text) |
| `ttk.Entry(frame, width=30)` | Create a single-line text input box |
| `ttk.Button(frame, text="Add", command=add_student)` | Create a button; when clicked, it runs `add_student()` |
| `ttk.Treeview(...)` | Create a table (rows and columns) to show student list |
| `tree.insert("", tk.END, values=(...))` | Add one row to the table |
| `tree.get_children()` | Get all row IDs in the table (to clear or update) |
| `entry_name.get()` | Get the text currently in the "Name" entry field |
| `entry_name.delete(0, tk.END)` | Clear all text in the entry field |
| `messagebox.showinfo("Title", "Message")` | Show a small pop-up with OK button |
| `root.mainloop()` | Start the event loop so the window stays open and responds to clicks |

## How to Use the App

1. **Add:** Type Name, Roll No, Course, Contact and click **Add Student**.
2. **View:** All students appear in the table below.
3. **Update:** Click a row in the table, change the fields, then click **Update Student**.
4. **Delete:** Click a row, then click **Delete Student** and confirm.
5. **Clear:** Clears the input fields only (does not delete from the list).

## Data Storage

- Data is stored in a **list** named `students` in memory.
- Each student is a **dictionary**: `{"id", "name", "roll_no", "course", "contact"}`.
- When you close the app, data is not saved to file (you can add file save/load later).
