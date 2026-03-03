"""
STUDENT MANAGEMENT SYSTEM - Python Tkinter
==========================================
A simple GUI application to Add, View, Update, and Delete student records.
Each section is commented so you can understand and explain the code.
"""

import tkinter as tk
from tkinter import ttk, messagebox

# =============================================================================
# DATA STORAGE - We use a list to store student records (in-memory)
# Each student is a dictionary with: id, name, roll_no, course, contact
# =============================================================================
students = []
next_id = 1  # Auto-increment ID for each new student


# =============================================================================
# FUNCTION: Add a new student to the list
# =============================================================================
def add_student():
    global next_id
    
    # Get values from entry fields (get() returns the text user typed)
    name = entry_name.get().strip()
    roll_no = entry_roll.get().strip()
    course = entry_course.get().strip()
    contact = entry_contact.get().strip()
    
    # Validation - check if required fields are empty
    if not name or not roll_no:
        messagebox.showwarning("Warning", "Name and Roll Number are required!")
        return
    
    # Create a new student dictionary and add to list
    student = {
        "id": next_id,
        "name": name,
        "roll_no": roll_no,
        "course": course,
        "contact": contact
    }
    students.append(student)
    next_id += 1
    
    # Clear the input fields after adding
    clear_entries()
    
    # Refresh the table to show the new student
    refresh_table()
    
    messagebox.showinfo("Success", "Student added successfully!")


# =============================================================================
# FUNCTION: Clear all entry (input) fields
# =============================================================================
def clear_entries():
    entry_name.delete(0, tk.END)
    entry_roll.delete(0, tk.END)
    entry_course.delete(0, tk.END)
    entry_contact.delete(0, tk.END)


# =============================================================================
# FUNCTION: Refresh the Treeview table with current student list
# =============================================================================
def refresh_table():
    # Clear all existing rows in the table
    for item in tree.get_children(): # tree is the name of the table
        tree.delete(item)
    
    # Insert each student as a row in the table
    for s in students:
        tree.insert("", tk.END, values=(s["id"], s["name"], s["roll_no"], s["course"], s["contact"]))


# =============================================================================
# FUNCTION: When user selects a row, load that student's data into the form
# =============================================================================
def on_select(event):
    selected = tree.selection()
    if not selected:
        return
    
    # Get the selected row's values
    item = tree.item(selected[0])
    values = item["values"]
    
    # Clear and fill the entry fields
    clear_entries()
    entry_name.insert(0, values[1])   # name
    entry_roll.insert(0, values[2])   # roll_no
    entry_course.insert(0, values[3]) # course
    entry_contact.insert(0, values[4]) # contact


# =============================================================================
# FUNCTION: Update the selected student with new data from the form
# =============================================================================
def update_student():
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Warning", "Please select a student to update!")
        return
    
    # Get the ID of selected row (first column)
    item = tree.item(selected[0])
    student_id = item["values"][0]
    
    # Find the student in our list and update their data
    for s in students:
        if s["id"] == student_id:
            s["name"] = entry_name.get().strip()
            s["roll_no"] = entry_roll.get().strip()
            s["course"] = entry_course.get().strip()
            s["contact"] = entry_contact.get().strip()
            break
    
    refresh_table()
    clear_entries()
    messagebox.showinfo("Success", "Student updated successfully!")


# =============================================================================
# FUNCTION: Delete the selected student
# =============================================================================
def delete_student():
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Warning", "Please select a student to delete!")
        return
    
    if not messagebox.askyesno("Confirm", "Are you sure you want to delete this student?"):
        return
    
    item = tree.item(selected[0])
    student_id = item["values"][0]
    
    # Remove the student from the list
    global students
    students = [s for s in students if s["id"] != student_id]
    
    refresh_table()
    clear_entries()
    messagebox.showinfo("Success", "Student deleted successfully!")


# =============================================================================
# MAIN WINDOW SETUP
# =============================================================================
root = tk.Tk()
root.title("Student Management System")
root.geometry("700x500")
root.resizable(True, True)

# =============================================================================
# FRAME 1: Input Form (Labels + Entry fields)
# =============================================================================
frame_form = ttk.LabelFrame(root, text="Student Details", padding=10)
frame_form.pack(fill=tk.X, padx=10, pady=5)

# Labels and Entry widgets - grid layout
# Label: just text. Entry: single-line text input
ttk.Label(frame_form, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=3)
entry_name = ttk.Entry(frame_form, width=30)
entry_name.grid(row=0, column=1, padx=5, pady=3)

ttk.Label(frame_form, text="Roll No:").grid(row=1, column=0, sticky=tk.W, pady=3)
entry_roll = ttk.Entry(frame_form, width=30)
entry_roll.grid(row=1, column=1, padx=5, pady=3)

ttk.Label(frame_form, text="Course:").grid(row=2, column=0, sticky=tk.W, pady=3)
entry_course = ttk.Entry(frame_form, width=30)
entry_course.grid(row=2, column=1, padx=5, pady=3)

ttk.Label(frame_form, text="Contact:").grid(row=3, column=0, sticky=tk.W, pady=3)
entry_contact = ttk.Entry(frame_form, width=30)
entry_contact.grid(row=3, column=1, padx=5, pady=3)

# =============================================================================
# FRAME 2: Buttons (Add, Update, Delete, Clear)
# =============================================================================
frame_buttons = ttk.Frame(root, padding=5)
frame_buttons.pack(fill=tk.X, padx=10)

ttk.Button(frame_buttons, text="Add Student", command=add_student).pack(side=tk.LEFT, padx=3)
ttk.Button(frame_buttons, text="Update Student", command=update_student).pack(side=tk.LEFT, padx=3)
ttk.Button(frame_buttons, text="Delete Student", command=delete_student).pack(side=tk.LEFT, padx=3)
ttk.Button(frame_buttons, text="Clear", command=clear_entries).pack(side=tk.LEFT, padx=3)

# =============================================================================
# FRAME 3: Table (Treeview) to display all students
# =============================================================================
frame_table = ttk.LabelFrame(root, text="Student List", padding=5)
frame_table.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

# Treeview: table with columns. show="headings" hides the first tree column
columns = ("id", "name", "roll_no", "course", "contact")
tree = ttk.Treeview(frame_table, columns=columns, show="headings", height=10)

# Define column headers and width
tree.heading("id", text="ID")
tree.heading("name", text="Name")
tree.heading("roll_no", text="Roll No")
tree.heading("course", text="Course")
tree.heading("contact", text="Contact")

tree.column("id", width=50)
tree.column("name", width=150)
tree.column("roll_no", width=80)
tree.column("course", width=120)
tree.column("contact", width=120)

# Scrollbar for the table
scrollbar = ttk.Scrollbar(frame_table)
tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
tree.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=tree.yview)

# Bind: when user clicks a row, call on_select to load data into form
tree.bind("<<TreeviewSelect>>", on_select)

# =============================================================================
# Start the application (event loop)
# =============================================================================
root.mainloop()
