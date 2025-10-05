import os
import sys
import logging

import CTkXYFrame

from customtkinter import *
from components.user_menu import userMenu
from components.audio_menu import audioMenu, plotAudio
from components.utils import createButton, lockItem, unlockItem
from components.error_handler import global_error_handler, show_error_popup
from components.constants import WIDTH, HEIGHT, SETTINGS_FILE

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("app.log", mode="w")
    ]
)

logger = logging.getLogger("SpeechTranscription")
logger.info("Starting SpeechTranscription app")

# Setup language_tool_python safely
try:
    import language_tool_python
    java_home = os.environ.get("JAVA_HOME", "")
    java_bin = os.path.join(java_home, "bin", "java.exe") if java_home else "java"
    tool = language_tool_python.LanguageTool(
        'en-US',
        progress_bar=False,
        config={'java_bin': java_bin}
    )
except Exception as e:
    logger.warning(f"LanguageTool not initialized: {e}")
    tool = None

class mainGUI(CTk):
    @global_error_handler
    def new_session(self):
        from datetime import datetime
        session_number = self.currentAudioNum + 1
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session_name = f"Session {session_number} - {current_time}"

        self.audioMenuList.append(audioMenu(self))
        newButton = createButton(self.userFrame.audioTabs, session_name, len(self.audioButtonList), 0,
                                 lambda x=self.currentAudioNum: self.changeAudioWindow(x),
                                 width=self.userFrame.audioTabs.cget("width"), lock=False)
        self.audioButtonList.append(newButton)
        self.changeAudioWindow(self.currentAudioNum)
        self.currentAudioNum += 1
        lockItem(self.showGraphButton)

    @global_error_handler
    def changeAudioWindow(self, num):
        for i, frame in enumerate(self.audioMenuList):
            if i == num:
                self.audioFrame = frame
                frame.grid(row=0, column=1, padx=5)
                if frame.audio.filePath:
                    unlockItem(self.showGraphButton)
                else:
                    lockItem(self.showGraphButton)
            else:
                frame.grid_remove()
        for i, button in enumerate(self.audioButtonList):
            button.configure(fg_color="#029CFF" if i == num else "#0062B1")
        self.tkraise(self.audioFrame)

    @global_error_handler
    def showHelpOverlay(self):
        popup = CTkToplevel(self)
        popup.title("Help Guide")
        popup.geometry("450x450")
        popup.attributes("-topmost", True)
        popup.resizable(False, False)

        helpText = """
        Help Guide:
        - New Audio: Create a new audio session.
        - Upload: Upload an audio file.
        - Record: Record a new audio file.
        - <<: Rewind by 5 seconds.
        - ⏯: Play/Pause audio.
        - >>: Fast forward 5 seconds.
        - Transcribe: Transcribe audio.
        - Label Speakers: Label speakers.
        - Apply Aliases: Customize speaker aliases.
        - Download Audio: Download audio.
        - Export to Word: Export transcription.
        - Grammar Check: Check grammar (needs LanguageTool).
        - Add Morphemes: Add morphemes after grammar check.
        - Submit: Submit grammar corrections.
        - Clear Box?: Clear transcription/convention box.
        - Lock/Unlock: Lock/unlock transcription/convention box.
        """

        helpLabel = CTkLabel(popup, text=helpText, justify=LEFT, font=("Arial", 12), wraplength=400)
        helpLabel.pack(padx=10, pady=10)

        closeButton = createButton(popup, "Close", None, None, popup.destroy, height=30, width=80, lock=False)
        closeButton.pack(pady=10)

    @global_error_handler
    def showAudioGraph(self):
        if hasattr(self, 'audioMenuList') and self.audioMenuList:
            current_audio_menu = self.audioMenuList[self.currentAudioNum - 1]
            if current_audio_menu.audio.filePath:
                time, signal = current_audio_menu.audio.createWaveformFile()
                plotAudio(time, signal)
            else:
                show_error_popup("No Audio File", "Upload or record audio first.")
        else:
            show_error_popup("No Session Available", "Create a session first.")

    def __init__(self):
        super().__init__()
        self.WIDTH = WIDTH
        self.HEIGHT = HEIGHT

        self.after(100, lambda: self.geometry("1375x740"))
        self.currentAudioNum = 0
        self.audioButtonList = []
        self.audioMenuList = []
        self.title('Speech Transcription')

        try:
            if os.path.getsize(SETTINGS_FILE) != 0:
                with open(SETTINGS_FILE, "r") as file:
                    set_appearance_mode(file.read())
            else:
                set_appearance_mode("dark")
        except FileNotFoundError:
            set_appearance_mode("dark")

        set_default_color_theme("blue")
        deactivate_automatic_dpi_awareness()
        self.resizable(False, False)
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")

        self.userFrame = userMenu(master=self)
        self.userFrame.grid(row=0, column=0, padx=1, sticky=NW)

        self.newSessionButton = createButton(self.userFrame, "New Session", 1, 0, self.new_session, 
                                             height=60, columnspan=2, lock=False)
        self.audioFrame = CTkFrame(self)

        self.helpButton = createButton(self, "Help", None, None, self.showHelpOverlay, 
                                     height=30, width=80, lock=False)
        self.helpButton.place(relx=0, rely=1, anchor=SW, x=10, y=-10)

        self.showGraphButton = createButton(self, "Show Audio Graph", None, None, self.showAudioGraph, 
                                            height=30, width=120, lock=True)
        self.showGraphButton.place(relx=0, rely=1, anchor=SW, x=110, y=-10)

        self.mainloop()

if __name__ == "__main__":
    try:
        headless = os.environ.get("HEADLESS", "false").lower() == "true"
        if headless:
            logger.info("Running in headless mode.")
            mainGUI()
        else:
            mainGUI()
    except Exception as e:
        logger.exception("Error running GUI.")
        raise
