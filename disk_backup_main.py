#!/usr/bin/python3

import gi, re, signal, time
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject
from multiprocessing import Process, Queue
from os import kill, path, mkdir, rmdir
import disk_backup_worker


class MainApp():

    def __init__(self):
        self.src = ""
        self.dest = ""
        
        self.q = Queue()
        self.today = time.strftime("%Y-%m-%d")


    """ GUI handler section """
    def on_delete_window(self, *args):
        Gtk.main_quit(*args)

    def on_entry_owner_changed(self, entry_owner):
        text = entry_owner.get_text()
        try:
            check = re.match('[a-zA-Z0-9-]*$', text).group(0)
        except AttributeError:
            check = ""
        if check is not "":
            self.owner = text
        else:
            self.owner = ""

    def on_source_set(self, button_source):
        self.gather_input("button_source")

    def on_dest_parent_set(self, button_dest_parent):
        prev_dir = self.dest
        try:
            rmdir(prev_dir)
        except FileNotFoundError:
            pass
        self.gather_input("button_dest_parent")

    def on_backup_button_pressed(self, button_backup):
        text = button_backup.get_label()
        if text == "Make Backup":
            button_backup.set_label("Cancel Backup")
            self.run_worker()
        elif text == "Cancel Backup":
            self.cancel_worker()

    def on_quit_button_pressed(self, button_quit):
        if self.dest is not "" and path.isdir(self.dest):
            try:
                rmdir(self.dest)
            except OSError:
                pass
        Gtk.main_quit()


    """ Main function section. """
    def gather_input(self, button):
        # This handles user input for both source dir and dest parent dir.
        d = [""] * 3
        user_input = builder.get_object(button).get_filename()
        if button == "button_source":
            self.src = user_input
        elif button == "button_dest_parent":
            d[0] = user_input
            d[1] = self.owner
            d[2] = self.today
            
            self.dest = d[0]+"/BACKUP-"+d[1]+"-"+d[2]

            summ = builder.get_object("label_summary")
            summ.set_label("<b>Backing up to: </b>"+self.dest)
            
        self.user_input_check(self.src, d[0], self.dest)
            
    def user_input_check(self, src, dest_parent, dest):
        s, p, d = 0, 0, 0
        
        if src is not "":
            s = 1 # A source directory has been chosen.

        if dest_parent is not "":
            p = 1 # The destination parent has been chosen.
        
        try:
            mkdir(dest)
        except (FileNotFoundError, FileExistsError):
            pass
        if path.isdir(dest):
            d = 1 # The destination directory has been created.
        
        if s * p * d == 1:
            # Ready for backup.
            button = builder.get_object("button_backup")
            button.set_sensitive(True)
    
    def run_worker(self):
        # Launch backup tasks in 2nd process. ("p0" is main process.)
        self.p1 = Process(
            target=disk_backup_worker.worker,
            args=(self.q, self.src, self.dest)
            )
        self.p1.start()
        # Get pid to kill process if necessary.
        self.worker_pid = self.p1.pid
        # Receive file count from backup process.
        self.total = self.q.get()
        # Check process state and progress.
        self.run_proc_check()

    def cancel_worker(self):
        kill(self.worker_pid, signal.SIGTERM) # or signal.SIGKILL

    def run_proc_check(self):
        # Get progress data using 3rd process
        self.p2 = Process(
            target=disk_backup_worker.file_count,
            args=(self.q,self.dest)
            )
        self.p2.start()
        # Receive current count of files copied from process.
        self.count = self.q.get()
        # Send data to progress bar
        self.prog = self.count / self.total
        builder.get_object("progress_backup").set_fraction(self.prog)
        
        # Check if backup is still running
        if (self.p1.is_alive()):
            # Set delay before checking again
            GObject.timeout_add(100, self.run_proc_check)
            return
        else:
            button = builder.get_object("button_backup")
            button.set_label("Done")
            button.set_sensitive(False)


if __name__ == '__main__':

    # Use Gtk.Builder to import initial gui from Glade.
    my_path = path.dirname(__file__)
    glade_file = path.join(my_path, "disk_backup_gui.glade")
    builder = Gtk.Builder()
    builder.add_from_file(glade_file)
    builder.connect_signals(MainApp())

    window = builder.get_object("MainWindow")

    window.show_all()
    Gtk.main()
