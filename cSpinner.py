import sys
import threading
import time

class cSpinner(threading.Thread):
    """
        Print information in the same line, giving feedback to the user
        \details Prints a spinning text on the screen. Additional text may be attached as extra information. Extends the Thread class
    """
    chars = ["\\","|","/","-"]
    index = 0
    keeprunning = True
    paused = False;
    msg = ""


    def run(self):
        """
            \brief Start the thread
        """
        while self.keeprunning:
            if (not self.paused): self.__printing(self.chars[self.index%len(self.chars)]+" "+self.msg)
            time.sleep(0.1)
            self.index +=1

    def set_msg(self,text):
        """
            \brief Set the extra message to print
            \param text String to print
        """
        self.msg = text;
    
    def __printing(self,data):
        """
            \brief print the information to stdout
        """
        sys.stdout.write("\r\x1b[K"+data.__str__())
        sys.stdout.flush()

    def stop(self):
        """
            \brief Stop the print thread.
        """
        self.keeprunning = False

    def pause(self):
        """
            \brief Pause the print thread.
        """
        self.paused = True;

    def unpause(self):
        """
            \brief continue the print thread.
        """
        self.paused = False;
