import tkinter as tk
from tkinter import ttk, messagebox
students = []
id = 1

def add_students():
    global id
    name = entry_name.get().strip()   # get text from Name entry
    roll = entry_roll.get().strip()   # get text from Roll entry
    course = entry_course.get().strip()   # get text from Course entry
    contact = entry_contact.get().strip()   # get text from Contact entry
    if not name or not roll:
        messagebox.showwarning("Warning", "Name and Roll Number are required!")
        return
    student = {
        "id": id,
        "name" : name,
        "roll" : roll,
        "course" : course,
        "contact" : contact
    }
    students.append(student)
    id += 1
    messagebox.showinfo("Success", "Student added successfully!")





window = tk.Tk()
window.title("Student Management System")
window.geometry("500x500")
window.resizable(True, True) # allow the window to be resized and first parameter is for width and second parameter is for height
frame_form = ttk.LabelFrame(window, text="Student Details", padding=10)
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

frame_buttons = ttk.Frame(window, padding=5)
frame_buttons.pack(fill=tk.X, padx=10)
ttk.Button(frame_buttons,text='add student',command=add_students).pack(side=tk.LEFT, padx=3) 
window.mainloop()