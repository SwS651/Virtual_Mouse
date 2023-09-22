import threading
import VirtualMouse as VM
from PIL import Image,ImageTk
import tkinter as tk
import cv2
import pystray


class victual_mouse_GUI:
    def __init__(self):
        self.img_label = None
        self.isVisible = True


    def initial_trayicon(self):
        image = Image.open("VirtualMouse/mouse_activated.png")
        menu = (
            pystray.MenuItem("V Mouse", pystray.Menu(
                pystray.MenuItem("Enable/Disable", self.withdraw_window))
            ),
            pystray.MenuItem("Setting", pystray.Menu(
                pystray.MenuItem("Show/Hide", self.withdraw_window))
            ),
            pystray.MenuItem('Quit', self.quit_window)
        )

        self.icon = pystray.Icon("name", image, "title", menu)


    def initial_window(self):
        self.root = tk.Tk()
        self.window_width = 120
        self.window_height = 35
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', 'true')
        self.setup_position('bottom_right')
        self.setup_dragging()
        self.set_image('VirtualMouse/mouse_deactivated.png', (30, 30))
        self.set_text('Hello')


    

    def setup_dragging(self):
        self.prev_x = self.prev_y = 0
        self.root.bind("<Double-Button-1>", self.withdraw_window)
        self.root.bind("<ButtonPress-1>", self.on_drag_start)
        self.root.bind("<B1-Motion>", self.on_drag_motion)


    # Window Moving Feature
    def on_drag_start(self, event):
        self.prev_x = event.x_root
        self.prev_y = event.y_root

    def on_drag_motion(self, event):
        new_x = self.root.winfo_x() + (event.x_root - self.prev_x)
        new_y = self.root.winfo_y() + (event.y_root - self.prev_y)
        self.root.geometry(f"+{new_x}+{new_y}")
        self.prev_x = event.x_root
        self.prev_y = event.y_root

    def show_window(self):
        self.root.after(0, self.root.deiconify)

    def withdraw_window(self,event):
        if self.isVisible:
            self.root.withdraw()
        else:
            self.root.deiconify()


        self.isVisible = not self.isVisible


    def quit_window(self):
        if self.root:
            self.root.after(10, self.root.destroy)
        if self.icon:
                self.icon.stop()

    
    def setup_position(self, position = 'default', offset_x = 0,offset_y = 0):
        if position == 'default':
            return
        
        screen_width = self.root.winfo_screenwidth()
        screen_height= self.root.winfo_screenheight()
        
        if position == 'top_left':
            offset_x = 0
            offset_y = 0

        elif position == 'center':
            offset_x = int((screen_width/2) - (self.window_width/2)) if offset_x == 0 else offset_x
            offset_y = int((screen_height/2) - (self.window_height/2)) if offset_y == 0 else offset_y

        elif position == 'top_right':
            offset_x = (screen_width - self.window_width - 15) if offset_x == 0 else offset_x
            offset_y = offset_y if offset_y != 0 else 0

        elif position == 'bottom_left':
            offset_x = offset_x if offset_x != 0 else 0
            offset_y = (screen_height - self.window_height * 3) if offset_y == 0 else offset_y

        elif position == 'bottom_right':
            offset_x = (screen_width - self.window_width - 15) if offset_x == 0 else offset_x
            offset_y = (screen_height - self.window_height * 3) if offset_y == 0 else offset_y

        self.root.geometry(f"{self.window_width}x{self.window_height}+{offset_x}+{offset_y}")

    def set_image(self, img_path, img_size = (100,100)):
        self.img_path = img_path
        self.img_size = img_size
    
    def set_text(self,text_status=''):
        self.text_status = text_status
        

    def update_gui_periodically(self):
        # This method periodically updates the GUI
        self.update_gui()
        self.root.after(100, self.update_gui_periodically)
        
    def update_gui(self):
        if self.img_path:
            img = Image.open(self.img_path).resize(self.img_size)
            img = ImageTk.PhotoImage(img)
            if self.img_label:
                self.img_label.configure(image=img)
                self.img_label.image = img  # Keep a reference to the image
            else:
                self.img_label = tk.Label(self.root, image=img)
                self.img_label.grid(column=0, row=0, sticky=tk.EW, padx=2)
                self.img_label.image = img  # Keep a reference to the image
        else:
            if self.img_label:
                self.img_label.configure(image=None)
                self.img_label.image = None
        self.text_label = tk.Label(self.root, text=self.text_status, font=("Arial", 12))
        self.text_label.grid(column=1, row=0, sticky=tk.W)

    def update_text(self):
        self.text_label.config(text=self.text_status)
    def update_image(self):
        img = Image.open(self.img_path).resize(self.img_size)
        img = ImageTk.PhotoImage(img)
        self.img_label.config(image=img)

    def tray_run(self):
        self.initial_trayicon()
        if self.icon:
            self.icon.run()

    def window_run(self):
        self.initial_window()
        self.update_gui()
        self.update_gui_periodically()
        self.root.mainloop()




looping_flag = True
cap = cv2.VideoCapture(0)
cap.set(3, 320)
cap.set(4, 240)
def virtual_mouse(vm_GUI):
    global looping_flag

    hand_tracking_controller = VM.VirtualMouseController()
    while looping_flag:
        _, img = cap.read()
        
        hand_tracking_controller.tracking(img)

        if hand_tracking_controller.get_mouse_status():

            vm_GUI.set_text(hand_tracking_controller.get_selected_mode())
            vm_GUI.set_image('VirtualMouse\mouse_activated.png',(30,30))
            
            
        else:
            vm_GUI.set_text('Enabled')
            vm_GUI.set_image('VirtualMouse\mouse_deactivated.png',(30,30))


        vm_GUI.root.after(10,vm_GUI.update_text)
        vm_GUI.root.after(100,vm_GUI.update_image)

        cv2.waitKey(1)

    


if __name__ in '__main__':
    vm_GUI = victual_mouse_GUI()
    t1 = threading.Thread(target=vm_GUI.tray_run,args=())
    t1.start()
    t2 = threading.Thread(target=virtual_mouse, args=(vm_GUI,))
    t2.daemon =True
    t2.start()
    vm_GUI.window_run()

    # Ensure proper thread termination
    looping_flag = False
    


    # t1.join()
    if t1.is_alive():
        print('T1 still alive')
    else:
        print('t1 closed')


    # t2.join()  # Wait for t2 to finish
    if t2.is_alive():
        print('T2 still running')
    else:
        print("T2 CLosed")

    print('End Main Thread')