import sys
import os
import re
import threading  
from PyQt6.QtCore import Qt, QTimer, QPoint, pyqtSignal,QMetaObject, pyqtSlot, QSize
from PyQt6 import QtCore
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTextEdit, QTextBrowser, QLabel, QGraphicsDropShadowEffect
from PyQt6.QtWidgets import QPushButton, QLabel, QInputDialog, QDialog, QFormLayout, QStackedLayout, QLineEdit, QMenu, QFileDialog, QSpacerItem, QSizePolicy
from PyQt6.QtGui import QFont, QPixmap, QAction, QIcon
from alphageist.query import query_vectorstore
from alphageist.vectorstore import create_vectorstore, vectorstore_exists, load_vectorstore
from alphageist.callbackhandler import CustomStreamHandler
from langchain.vectorstores.base import VectorStore
from dotenv import load_dotenv
from langchain.schema import LLMResult

TEST_DATA_PATH = "test/data"
PERSIST_DIRECTORY = ".alphageist"

_icon_by_filetype = {
    ".txt": "txt.png",
    ".pdf": "pdf.png",
    ".csv": "csv.png",
    ".py": "python.png",
    ".go": "golang.png",
    ".pptx": "pptx.png",
    ".docx": "word.png",
    "default": "default_file.png"
}

def _get_image_path_by_filename(filename:str)->str:
    _, file_extension = os.path.splitext(filename)
    return _icon_by_filetype.get(file_extension, _icon_by_filetype["default"])

class SettingsDialog(QDialog):
    
    # Connected to focus check of Settings window 
    opened = pyqtSignal()
    closed = pyqtSignal()

    def __init__(self, api_key, search_folder):
        
        super().__init__()
        self.setWindowTitle("Settings")
        self.setModal(True)  # Set the dialog to be application modal
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)  # Add the "stay on top" window flag
        self.api_key = api_key
        self.search_folder = search_folder
        self.init_ui()

    def init_ui(self):
        
        self.init_api_key_settings()    # Set "API key" field
        self.init_search_folder()       # Set "Add search folder" container
        self.init_delete_button()       # Set "Delete" button
        self.init_edit_button()         # Set "Edit" button
        self.init_add_folder_button()   # Set "Add folder" button 
        self.init_save_button()         # Set "Save" button
        self.init_saved_folder_path()    # Set previously saved folder (if it exists)
        self.init_layout()              # Set main layout

    def init_api_key_settings(self):
        # Set the API key input row
        
        # Set API key input field 
        self.api_key_input = QLineEdit(self)
        self.api_key_input.setText(self.api_key)
        self.api_key_input.setReadOnly(True)
        self.api_key_input.textChanged.connect(self.update_save_button_state)
        self.api_key_input.setMinimumSize(450, 0)
        self.api_key_input.setFixedHeight(30)  # Set the height
        self.api_key_input.setStyleSheet(
            """
                color: gray;
                border-radius: 10px;
            """
            ) 

        # Set edit button for API key field
        self.api_key_edit = QPushButton('✎', self)
        self.api_key_edit.clicked.connect(self.toggle_api_key_edit)
        self.api_key_edit.setStyleSheet(
            """
                color: white; 
                background-color: #629EE4;
                border-radius: 10px;
            """
            )
        self.api_key_edit.setFixedWidth(40) 
        self.api_key_edit.setFixedHeight(30)  

        # Set horisontal layout for API key row
        self.api_key_layout = QHBoxLayout()
        self.api_key_layout.addWidget(QLabel("API Key"))
        self.api_key_layout.addWidget(self.api_key_input)
        self.api_key_layout.addWidget(self.api_key_edit)

    def init_search_folder(self):
        # Set the Search folder container which holds a folder icon and path to chosen search folder 

        # Set folder display container
        self.folder_container = QWidget(self)
        self.folder_container.setStyleSheet(
            """
            background-color: #252525; 
            border-radius: 10px;
            """
        )
        self.folder_container.setFixedWidth(500)
        self.folder_container.setFixedHeight(40)

        # Add drop shadow effect to folder container
        shadow_effect = QGraphicsDropShadowEffect(self.folder_container)
        shadow_effect.setBlurRadius(15)
        shadow_effect.setOffset(2)
        shadow_effect.setColor(Qt.GlobalColor.black)  # Set shadow color
        self.folder_container.setGraphicsEffect(shadow_effect)

        # Initially hide the folder display container
        self.folder_container.hide()

        # Set layout for folder display container
        folder_layout = QHBoxLayout(self.folder_container)
        folder_layout.setContentsMargins(10, 0, 0, 0)  # Margins left, top, right, bottom
        folder_layout.setSpacing(10)  # Spacing between elements in layout

        # Set folder icon
        folder_icon = QLabel(self.folder_container)
        folder_icon_path = os.path.join("frontend_assets", "folder_icon_1200x1200.png")
        folder_icon.setPixmap(QPixmap(folder_icon_path).scaled(25, 25, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        folder_icon.setFixedSize(25, 25)
        folder_layout.addWidget(folder_icon)

        # Set folder path text field
        self.folder_path = QLineEdit(self.folder_container)
        self.folder_path.setStyleSheet("color: white;")
        self.folder_path.setReadOnly(True)
        self.folder_path.textChanged.connect(self.update_save_button_state)
        folder_layout.addWidget(self.folder_path)

    def init_delete_button(self):
        # Set the search folder delete button 
        self.delete_folder_button = QPushButton(self)
        delete_folder_icon_path = os.path.join("frontend_assets", "trash_can_1200x1200.png")
        self.delete_folder_button.setIcon(QIcon(QPixmap(delete_folder_icon_path))) 
        self.delete_folder_button.setIconSize(QSize(25, 25))
        self.delete_folder_button.setStyleSheet(
            """
            background-color: #E06060; 
            border-radius: 10px;
            """
        )
        self.delete_folder_button.setFixedWidth(35)  
        self.delete_folder_button.setFixedHeight(35)  
        self.delete_folder_button.clicked.connect(self.remove_folder)
        self.delete_folder_button.hide() # Initially hide the button

    def init_edit_button(self):
        # Set the edit search folder button
        self.edit_folder_button = QPushButton('✎', self)
        self.edit_folder_button.setStyleSheet(
            """
                color: white; 
                background-color: #629EE4;
                border-radius: 10px;
            """
            )
        self.edit_folder_button.setFixedWidth(35)  
        self.edit_folder_button.setFixedHeight(35)  
        self.edit_folder_button.clicked.connect(self.add_folder)
        self.edit_folder_button.hide() # Initially hide the button

    def init_add_folder_button(self):
        # Set the add folder button
        self.add_folder_button = QPushButton('+ Add', self)
        self.add_folder_button.clicked.connect(self.add_folder)
        self.add_folder_button.setStyleSheet(
            """
            background-color: #629EE4; 
            border-radius: 10px;
            """
        )
        self.add_folder_button.setFixedWidth(70)
        self.add_folder_button.setFixedHeight(30)

    def init_save_button(self):
        # Set save button design and intial state 
        self.save_button = QPushButton('Save', self)
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.save_and_close)
        self.save_button.clicked.connect(self.accept)
        self.save_button.setFixedHeight(30)
        self.save_button.setFixedWidth(150)  

        self.save_button.setStyleSheet(
        """
            QPushButton {
                border-radius: 10px; 
                color: #9E9E9E;
            }
            QPushButton:enabled {
                background-color: #629EE4;
                color: white;
            }
            QPushButton:!enabled {
                background-color: #565656;
            }
        """
        )

    def init_layout(self):

        # Set the vertical layout inside the settings window
        self.layout = QVBoxLayout()

        # Add API key layout to main layout
        self.layout.addLayout(self.api_key_layout)

        # Create empty space after the API key row
        spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.MinimumExpanding)
        self.layout.addItem(spacer)

        # Add "Choose Folders" label
        self.layout.addWidget(QLabel("Choose Folders"))

        # Set horisontal layout for "Search Folder container" with edit & delete button
        self.folder_display_layout = QHBoxLayout()
        self.folder_display_layout.addWidget(self.folder_container) # Add search folder container 
        self.folder_display_layout.addWidget(self.edit_folder_button) # Add edit button
        self.folder_display_layout.addWidget(self.delete_folder_button) # Add delete button
        
        # Add "Search folder container" to main layout
        self.layout.addLayout(self.folder_display_layout)

        # Add "Add button" to main layout 
        self.layout.addWidget(self.add_folder_button)

        # Add empty space after the "Add folder" row
        self.layout.addItem(spacer)

        # Add "Save button" to main layout
        self.layout.addWidget(self.save_button)

        # Set main layout
        self.setLayout(self.layout)

    def update_save_button_state(self):
        # Update state on the "Save button" if user has made any changes in the Settings window 
        if (self.api_key_input.text() != self.api_key or self.folder_path.text() != self.search_folder):
            self.save_button.setEnabled(True)
        else:
            self.save_button.setEnabled(False)
    
    def save_and_close(self):
        # Add changes made in the settings window 

        # Emit the 'closed' signal and close the window
        self.closed.emit()
        self.close()

    def toggle_api_key_edit(self):
        # When user want to edit the API key field
        self.api_key_input.setReadOnly(not self.api_key_input.isReadOnly())
        self.api_key_input.setStyleSheet("color: white;") # Change color of text in field

    def init_saved_folder_path(self):
        # Check if any search folders has been previously saved 
        if self.search_folder:
            self.folder_path.setText(self.search_folder)
            self.folder_container.show()
            self.delete_folder_button.show()
            self.edit_folder_button.show()
            self.add_folder_button.hide()
        else:
            self.folder_container.hide()
    
    def add_folder(self):
        # Lets user choose a search folder via a file dialog window, after pressing on the "+Add" button
        self.added_folder_path = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        if self.added_folder_path:
            self.folder_path.setText(self.added_folder_path)
            self.folder_container.show()
            self.delete_folder_button.show()
            self.edit_folder_button.show()
            self.add_folder_button.hide()
            self.update_save_button_state()
        else:
            self.folder_container.hide()

    def remove_folder(self):
        # Removes chosen search folder, after user has pressed on the trash can button (aka "delete button")
        self.folder_path.clear()
        self.folder_container.hide()
        self.delete_folder_button.hide()
        self.edit_folder_button.hide()
        self.add_folder_button.show()
        self.update_save_button_state()

    def showEvent(self, event):
        self.opened.emit()

    def closeEvent(self, event):
        self.closed.emit()



class SpotlightSearch(QWidget):

    vectorstore: VectorStore 
    _loading_vectorstore: bool = False 
    update_search_results_signal = pyqtSignal(str)

    def __init__(self, path): 
        super().__init__()
        self.mpos = QPoint()
        self.settings_open = False
        self.search_folder_path = path
        
        # Load vectorstore on a separate thread
        if vectorstore_exists(PERSIST_DIRECTORY):
            self.vectorstore = load_vectorstore(PERSIST_DIRECTORY)
        else:
            self._loading_vectorstore = True
            vectorstore_loading_thread = threading.Thread(target=self._create_vectorstore, args=(path,PERSIST_DIRECTORY))
            vectorstore_loading_thread.daemon = True
            vectorstore_loading_thread.start()

        # Set up the user interface
        self.init_ui()

        # Set up the timer for checking focus
        self.check_focus_timer = QTimer(self)
        self.check_focus_timer.timeout.connect(self.check_focus)
        self.check_focus_timer.start(500)  

        # Set up the timer for checking if vectorstore i loaded
        self.vectorstore_status_timer = QTimer(self)
        self.vectorstore_status_timer.timeout.connect(self._check_vectorstore_status)
        self.vectorstore_status_timer.start(100)  

        self.setFocus() # Sets focus so the program wont shutdown

        # Set up the callback functionality making streaming possible
        self.init_callback()

    def init_callback(self):
        self.raw_response = [] 
        self.callback = CustomStreamHandler(self.on_llm_new_token, self.on_llm_end)
        self.muted = False
        
        self.update_search_results_signal.connect(self.update_search_results)

    @pyqtSlot(str)
    def update_search_results(self, text: str):
        self.search_results.setHtml(text)
        self.search_results.setVisible(True)
        self.adjust_window_size()
    
    def on_llm_new_token(self, token:str, **kwargs):
        if self.muted:
            return 
        if token == "OURCES" and self.raw_response[-1] == "S": 
            self.muted = True
            self.raw_response.pop()
            self.update_search_results_signal.emit(''.join(self.raw_response))
            
        else: 
            self.raw_response.append(token)

        response:str = ''.join(self.raw_response).replace('\n', '<br>')
        self.update_search_results_signal.emit(response)
        QMetaObject.invokeMethod(self, "update_search_results_signal", QtCore.Qt.ConnectionType.QueuedConnection, QtCore.Q_ARG(str, response))

        self.search_results.setVisible(True)
        self.adjust_window_size()

    def _get_sources_from_answer(self, answer:str) -> list[str]:
        if re.search(r"SOURCES:\s", answer):
            _, sources = re.split(r"SOURCES:\s", answer)
        else:
            sources = ""
        return sources.split(',')

    def on_llm_end(self, response:LLMResult, **kwargs) -> None:
        answer = response.generations[0][0].text
        sources = self._get_sources_from_answer(answer) 

        # Append sources to the search result text
        search_result_text = self.search_results.toHtml()

        search_result_text += "Sources:"
        search_result_text += "<table>"
        for source in sources:
            icon_path = "frontend_assets/" + _get_image_path_by_filename(source)
            search_result_text += f"""<tr>
<td style='padding-right: 4px;'>
<img src='{icon_path}' width='16' height='16' style='vertical-align: middle;' />
</td>
<td>
<a href='{source.strip()}'>{source.strip()}</a>
</td>
</tr>"""

        search_result_text += "</table>"

        self.update_search_results_signal.emit(search_result_text)
        QMetaObject.invokeMethod(self, "update_search_results_signal", QtCore.Qt.ConnectionType.QueuedConnection, QtCore.Q_ARG(str, search_result_text))

        self.muted = False
        self.raw_response = []

    def _check_vectorstore_status(self):
        if self._loading_vectorstore:
            self.search_bar.setPlaceholderText("Loading vectorstore...")
            self.search_bar.setEnabled(False)
        else: 
            self.search_bar.setPlaceholderText("Search...")
            self.search_bar.setEnabled(True)
    
    def _create_vectorstore(self, path, persist_vectorstore):
       self.vectorstore = create_vectorstore(path, persist_vectorstore) 
       self._loading_vectorstore = False

    def init_ui(self):
        # Set window properties
        self.set_window_properties()

        # Set up the user interface
        layout = QVBoxLayout()
        layout.addLayout(self.create_search_layout())

        # Create text browser to display search results
        self.create_search_results()
        layout.addWidget(self.search_results)

        # Set the layout for the widget
        self.setLayout(layout)

        # Add drop shadow effect
        self.add_shadow_effect()

    def set_window_properties(self):
        self.setMinimumSize(600, 100)
        self.setMaximumSize(600, 100)
        self.center()

        # Remove window frame and background
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def create_search_layout(self):
        # Create a horizontal layout for search bar and logo
        search_layout = QHBoxLayout()
        search_layout.setSpacing(2)  # Set spacing between logo and search bar

        # Create logo label and load logo image
        self.create_logo_label()
        search_layout.addWidget(self.logo_label)

        # Create search bar and set properties
        self.create_search_bar()
        search_layout.addWidget(self.search_bar)

        return search_layout

    def create_logo_label(self):
        self.logo_label = QLabel(self)
        logo_path = os.path.join("frontend_assets", "logo2_45x45.png")
        logo_pixmap = QPixmap(logo_path)
        self.logo_label.setPixmap(logo_pixmap.scaled(45, 45, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))  # Adjust logo size

        # Create context menu for logo_label
        self.logo_label.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.logo_label.customContextMenuRequested.connect(self.show_logo_context_menu)
        self.settings_action = QAction("Settings", self)
        self.settings_action.triggered.connect(self.show_settings)

    def create_search_bar(self):
        self.search_bar = QLineEdit(self)
        font = QFont()
        font.setPointSize(20)  # Set size font of search bar text
        self.search_bar.setFont(font)
        self.search_bar.setFixedHeight(42)  # Adjust the height of search bar
        self.search_bar.setPlaceholderText("Search...")  # Set default text in Search bar
        self.search_bar.returnPressed.connect(self.search)

    def create_search_results(self):
        self.search_results = QTextBrowser(self)
        self.search_results.setOpenExternalLinks(True)
        self.search_results.setVisible(False)  # Hide search result initially
        self.search_results.setStyleSheet(
            """
            QTextBrowser {
            border: 1px solid #686868;
            border-radius: 10px;
            background-color: #323232;
            }
            """
        )

    def add_shadow_effect(self):
        self.shadow_effect = QGraphicsDropShadowEffect()
        self.shadow_effect.setBlurRadius(20)
        self.shadow_effect.setOffset(0, 0)
        self.setGraphicsEffect(self.shadow_effect)

    def center(self):
        """
        Centers the main window of the application on the screen.
        
        This method calculates the center position of the screen based on the
        screen geometry and the window geometry. It then moves the window to
        that position.
        """
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        window_geometry = self.geometry()
        x = (screen_geometry.width() - window_geometry.width()) / 2
        y = (screen_geometry.height() - window_geometry.height()) / 2
        self.move(int(x), int(y))

    def check_focus(self):
        # Shut down if user start focusing on something else 
        if not self.settings_open and not self.hasFocus() and not self.search_bar.hasFocus() and not self.search_results.hasFocus():
            self.close()

    def search(self):
        if not self.search_bar.text():
            self.search_results.setVisible(False)
            self.adjust_window_size()
            return

        query_thread = threading.Thread(target=query_vectorstore, 
                                        args=(self.vectorstore, self.search_bar.text()), 
                                        kwargs={"callbacks":[self.callback]})
        query_thread.daemon = True
        query_thread.start()

    def show_settings(self):
        if hasattr(self, 'settings_dialog'): # If the settings dialog already exists, show it and don't create a new
            self.settings_dialog.show()
        else:
            self.settings_dialog = SettingsDialog("Yktgs45363twrwfdsgjryrehg6433", self.search_folder_path)
            self.settings_dialog.opened.connect(self.settings_opened)
            self.settings_dialog.closed.connect(self.settings_closed)
            self.settings_dialog.show()
    
    def show_logo_context_menu(self, position):
        context_menu = QMenu(self)
        context_menu.addAction(self.settings_action)
        context_menu.exec(self.logo_label.mapToGlobal(position))

    def settings_opened(self):
        self.settings_open = True

    def settings_closed(self):
        self.settings_open = False

    def adjust_window_size(self):
        if self.search_results.isVisible():
            self.setMinimumSize(600, 400)
            self.setMaximumSize(600, 400)
        else:
            self.setMinimumSize(600, 100)
            self.setMaximumSize(600, 100)

    def mousePressEvent(self, event):
        self.mpos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event): 
        # Enable user to drag around serach bar on screen 
        diff = event.globalPosition().toPoint() - self.mpos
        newpos = self.pos() + diff
        self.move(newpos)
        self.mpos = event.globalPosition().toPoint()

def main():
    # path = input("Path (test/data/):")
    # path = path if path else TEST_DATA_PATH

    app = QApplication(sys.argv)
    spotlight_search = SpotlightSearch(TEST_DATA_PATH)
    spotlight_search.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    load_dotenv()
    main()
