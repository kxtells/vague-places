import sys
import threading
import time

class cSpinner(threading.Thread):
    """
        Print things to one line dynamically
    """
    chars = ["\\","|","/","-"]
    index = 0
    keeprunning = True
    paused = False; 


    def run(self):
        while self.keeprunning:
            if (not self.paused): self.printing(self.chars[self.index%len(self.chars)])
            time.sleep(0.1)
            self.index +=1

    def printing(self,data):
        sys.stdout.write("\r\x1b[K"+data.__str__())
        sys.stdout.flush()

    def stop(self):
        self.keeprunning = False

    def pause(self):
        self.paused = True;

    def unpause(self):
        self.paused = False;
